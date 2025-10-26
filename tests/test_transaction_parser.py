"""
Unit tests for parser/transaction_parser.py
"""
import pytest
from io import BytesIO
from parser.transaction_parser import TransactionParser
from models.transaction import Transaction, TXInput, TXOutput, TXWitnessStack, TXWitnessStackItem


class TestParseInput:
    """Test parse_input function"""

    def test_parse_input_basic(self):
        """Test parsing a basic transaction input"""
        # Create a simple input: 32-byte txid, 4-byte vout, empty scriptSig, 4-byte sequence
        txid = b'\x01' * 32
        vout = b'\x02\x00\x00\x00'  # vout 2 in little-endian
        ss_size = b'\x00'  # compact size 0
        seq = b'\xff\xff\xff\xff'

        buffer = BytesIO(txid + vout + ss_size + seq)
        tx_input = TransactionParser.parse_input(buffer)

        assert tx_input.txid == txid
        assert tx_input.vout == vout
        assert tx_input.ss_size == 0
        assert tx_input.ss == b''
        assert tx_input.seq == seq

    def test_parse_input_with_scriptsig(self):
        """Test parsing input with scriptSig"""
        txid = b'\xaa' * 32
        vout = b'\x01\x00\x00\x00'
        ss = b'\x48\x30\x45'  # Sample scriptSig data
        ss_size = bytes([len(ss)])  # compact size
        seq = b'\xfe\xff\xff\xff'

        buffer = BytesIO(txid + vout + ss_size + ss + seq)
        tx_input = TransactionParser.parse_input(buffer)

        assert tx_input.txid == txid
        assert tx_input.vout == vout
        assert tx_input.ss_size == 3
        assert tx_input.ss == ss
        assert tx_input.seq == seq

    def test_parse_input_large_scriptsig(self):
        """Test parsing input with larger scriptSig"""
        txid = b'\xbb' * 32
        vout = b'\x05\x00\x00\x00'
        ss = b'\x12\x34\x56\x78' * 50  # 200 bytes
        ss_size = bytes([200])
        seq = b'\x00\x00\x00\x00'

        buffer = BytesIO(txid + vout + ss_size + ss + seq)
        tx_input = TransactionParser.parse_input(buffer)

        assert tx_input.txid == txid
        assert tx_input.ss_size == 200
        assert len(tx_input.ss) == 200
        assert tx_input.ss == ss

    def test_parse_input_buffer_position(self):
        """Test that buffer position advances correctly"""
        txid = b'\xcc' * 32
        vout = b'\x00\x00\x00\x00'
        ss_size = b'\x02'
        ss = b'\xaa\xbb'
        seq = b'\xff\xff\xff\xff'
        extra_data = b'\x99\x88\x77'

        buffer = BytesIO(txid + vout + ss_size + ss + seq + extra_data)
        tx_input = TransactionParser.parse_input(buffer)

        # Buffer should be positioned right after the input
        assert buffer.read(1) == b'\x99'


class TestParseOutput:
    """Test parse_output function"""

    def test_parse_output_basic(self):
        """Test parsing a basic transaction output"""
        amount = 50000  # satoshis
        amount_bytes = amount.to_bytes(8, byteorder='little')
        spk = b'\x76\xa9\x14'  # Sample scriptPubKey
        spk_size = bytes([len(spk)])

        buffer = BytesIO(amount_bytes + spk_size + spk)
        tx_output = TransactionParser.parse_output(buffer)

        assert tx_output.amount == amount
        assert tx_output.spk_size == 3
        assert tx_output.spk == spk

    def test_parse_output_zero_amount(self):
        """Test parsing output with zero amount"""
        amount_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        spk = b'\x00\x14'
        spk_size = bytes([len(spk)])

        buffer = BytesIO(amount_bytes + spk_size + spk)
        tx_output = TransactionParser.parse_output(buffer)

        assert tx_output.amount == 0
        assert tx_output.spk_size == 2
        assert tx_output.spk == spk

    def test_parse_output_large_amount(self):
        """Test parsing output with large amount (21M BTC in sats)"""
        amount = 2100000000000000  # 21M BTC
        amount_bytes = amount.to_bytes(8, byteorder='little')
        spk = b'\xa9\x14' + b'\x12' * 20 + b'\x87'  # P2SH-like
        spk_size = bytes([len(spk)])

        buffer = BytesIO(amount_bytes + spk_size + spk)
        tx_output = TransactionParser.parse_output(buffer)

        assert tx_output.amount == amount
        assert tx_output.spk_size == len(spk)

    def test_parse_output_p2wpkh_script(self):
        """Test parsing output with P2WPKH scriptPubKey"""
        amount = 100000000  # 1 BTC
        amount_bytes = amount.to_bytes(8, byteorder='little')
        # P2WPKH: OP_0 OP_PUSHBYTES_20 <20 bytes>
        spk = b'\x00\x14' + b'\xaa' * 20
        spk_size = bytes([len(spk)])

        buffer = BytesIO(amount_bytes + spk_size + spk)
        tx_output = TransactionParser.parse_output(buffer)

        assert tx_output.amount == amount
        assert tx_output.spk_size == 22
        assert tx_output.spk == spk

    def test_parse_output_buffer_position(self):
        """Test that buffer position advances correctly"""
        amount_bytes = (10000).to_bytes(8, byteorder='little')
        spk = b'\x76\xa9'
        spk_size = bytes([len(spk)])
        extra_data = b'\xde\xad\xbe\xef'

        buffer = BytesIO(amount_bytes + spk_size + spk + extra_data)
        tx_output = TransactionParser.parse_output(buffer)

        # Buffer should be positioned right after the output
        assert buffer.read(1) == b'\xde'


class TestParseWitness:
    """Test parse_witness function"""

    def test_parse_witness_single_input_empty_stack(self):
        """Test parsing witness data for single input with empty stack"""
        # Stack count = 0
        buffer = BytesIO(b'\x00')
        witness_stacks = TransactionParser.parse_witness(buffer, 1)

        assert len(witness_stacks) == 1
        assert len(witness_stacks[0].witness_items) == 0

    def test_parse_witness_single_input_one_item(self):
        """Test parsing witness data for single input with one stack item"""
        # Stack count = 1, item size = 3, item data
        item_data = b'\xaa\xbb\xcc'
        buffer = BytesIO(b'\x01\x03' + item_data)
        witness_stacks = TransactionParser.parse_witness(buffer, 1)

        assert len(witness_stacks) == 1
        assert len(witness_stacks[0].witness_items) == 1
        assert witness_stacks[0].witness_items[0].stack_item_size == 3
        assert witness_stacks[0].witness_items[0].stack_item == item_data

    def test_parse_witness_single_input_multiple_items(self):
        """Test parsing witness data with multiple stack items (typical P2WPKH)"""
        # P2WPKH has 2 items: signature and pubkey
        sig = b'\x30\x45' + b'\x02' * 70  # Simplified signature
        pubkey = b'\x02' + b'\x03' * 32  # Compressed pubkey

        buffer = BytesIO(
            b'\x02' +  # 2 stack items
            bytes([len(sig)]) + sig +
            bytes([len(pubkey)]) + pubkey
        )
        witness_stacks = TransactionParser.parse_witness(buffer, 1)

        assert len(witness_stacks) == 1
        assert len(witness_stacks[0].witness_items) == 2
        assert witness_stacks[0].witness_items[0].stack_item == sig
        assert witness_stacks[0].witness_items[1].stack_item == pubkey

    def test_parse_witness_multiple_inputs(self):
        """Test parsing witness data for multiple inputs"""
        # Input 1: 1 stack item
        item1 = b'\x01\x02\x03'
        # Input 2: 2 stack items
        item2a = b'\xaa'
        item2b = b'\xbb\xcc'

        buffer = BytesIO(
            b'\x01' + bytes([len(item1)]) + item1 +  # Input 1
            b'\x02' + bytes([len(item2a)]) + item2a + bytes([len(item2b)]) + item2b  # Input 2
        )
        witness_stacks = TransactionParser.parse_witness(buffer, 2)

        assert len(witness_stacks) == 2
        assert len(witness_stacks[0].witness_items) == 1
        assert witness_stacks[0].witness_items[0].stack_item == item1
        assert len(witness_stacks[1].witness_items) == 2
        assert witness_stacks[1].witness_items[0].stack_item == item2a
        assert witness_stacks[1].witness_items[1].stack_item == item2b

    def test_parse_witness_empty_stack_items(self):
        """Test parsing witness with empty stack items"""
        # 2 stack items, both empty
        buffer = BytesIO(b'\x02\x00\x00')
        witness_stacks = TransactionParser.parse_witness(buffer, 1)

        assert len(witness_stacks) == 1
        assert len(witness_stacks[0].witness_items) == 2
        assert witness_stacks[0].witness_items[0].stack_item_size == 0
        assert witness_stacks[0].witness_items[0].stack_item == b''
        assert witness_stacks[0].witness_items[1].stack_item_size == 0
        assert witness_stacks[0].witness_items[1].stack_item == b''

    def test_parse_witness_large_stack_item(self):
        """Test parsing witness with large stack item"""
        large_data = b'\xff' * 1000
        buffer = BytesIO(
            b'\x01' +  # 1 stack item
            b'\xfd\xe8\x03' +  # compact size for 1000
            large_data
        )
        witness_stacks = TransactionParser.parse_witness(buffer, 1)

        assert len(witness_stacks) == 1
        assert len(witness_stacks[0].witness_items) == 1
        assert witness_stacks[0].witness_items[0].stack_item_size == 1000
        assert len(witness_stacks[0].witness_items[0].stack_item) == 1000


class TestParseTransaction:
    """Test parse_transaction function"""

    def test_parse_transaction_legacy_simple(self):
        """Test parsing a simple legacy (non-SegWit) transaction"""
        version = b'\x01\x00\x00\x00'
        # 1 input
        input_count = b'\x01'
        txid = b'\xaa' * 32
        vout = b'\x00\x00\x00\x00'
        ss_size = b'\x00'
        seq = b'\xff\xff\xff\xff'
        # 1 output
        output_count = b'\x01'
        amount = (50000).to_bytes(8, byteorder='little')
        spk = b'\x76\xa9\x14' + b'\xbb' * 20 + b'\x88\xac'
        spk_size = bytes([len(spk)])
        # locktime
        locktime = b'\x00\x00\x00\x00'

        tx_data = (version + input_count + txid + vout + ss_size + seq +
                   output_count + amount + spk_size + spk + locktime)

        buffer = BytesIO(tx_data)
        tx = TransactionParser.parse_transaction(buffer)

        assert tx.version == version
        assert tx.witness_flag == b'\x00' or tx.witness_flag == 0
        assert len(tx.inputs) == 1
        assert len(tx.outputs) == 1
        assert len(tx.witness) == 0
        assert tx.locktime == locktime

    def test_parse_transaction_segwit_detection(self):
        """Test that SegWit transactions are detected correctly"""
        version = b'\x02\x00\x00\x00'
        marker = b'\x00'  # SegWit marker
        flag = b'\x01'  # SegWit flag
        # 1 input
        input_count = b'\x01'
        txid = b'\xcc' * 32
        vout = b'\x01\x00\x00\x00'
        ss_size = b'\x00'
        seq = b'\xfe\xff\xff\xff'
        # 1 output
        output_count = b'\x01'
        amount = (100000).to_bytes(8, byteorder='little')
        spk = b'\x00\x14' + b'\xdd' * 20  # P2WPKH
        spk_size = bytes([len(spk)])
        # witness data (1 input, 2 stack items for P2WPKH)
        witness = b'\x02\x47' + b'\x30' * 71 + b'\x21' + b'\x02' * 33
        # locktime
        locktime = b'\x00\x00\x00\x00'

        tx_data = (version + marker + flag + input_count + txid + vout + ss_size + seq +
                   output_count + amount + spk_size + spk + witness + locktime)

        buffer = BytesIO(tx_data)
        tx = TransactionParser.parse_transaction(buffer)

        assert tx.version == version
        assert tx.witness_flag == flag
        assert len(tx.witness) == 1
        assert tx.vbytes > 0

    def test_parse_transaction_multiple_inputs_outputs(self):
        """Test parsing transaction with multiple inputs and outputs"""
        version = b'\x01\x00\x00\x00'
        # 2 inputs
        input_count = b'\x02'
        input1 = b'\x11' * 32 + b'\x00\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff'
        input2 = b'\x22' * 32 + b'\x01\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff'
        # 2 outputs
        output_count = b'\x02'
        output1 = (30000).to_bytes(8, byteorder='little') + b'\x19' + b'\x76\xa9\x14' + b'\x33' * 20 + b'\x88\xac'
        output2 = (20000).to_bytes(8, byteorder='little') + b'\x16' + b'\x00\x14' + b'\x44' * 20
        # locktime
        locktime = b'\x10\x00\x00\x00'

        tx_data = version + input_count + input1 + input2 + output_count + output1 + output2 + locktime

        buffer = BytesIO(tx_data)
        tx = TransactionParser.parse_transaction(buffer)

        assert len(tx.inputs) == 2
        assert len(tx.outputs) == 2
        assert tx.locktime == locktime
        assert tx.inputs[0].txid == b'\x11' * 32
        assert tx.inputs[1].txid == b'\x22' * 32

    def test_parse_transaction_vbytes_calculation_legacy(self):
        """Test vbytes calculation for legacy transaction"""
        version = b'\x01\x00\x00\x00'
        input_count = b'\x01'
        txid = b'\xee' * 32
        vout = b'\x00\x00\x00\x00'
        ss_size = b'\x00'
        seq = b'\xff\xff\xff\xff'
        output_count = b'\x01'
        amount = (50000).to_bytes(8, byteorder='little')
        spk_size = b'\x19'
        spk = b'\x76\xa9\x14' + b'\xff' * 20 + b'\x88\xac'
        locktime = b'\x00\x00\x00\x00'

        tx_data = (version + input_count + txid + vout + ss_size + seq +
                   output_count + amount + spk_size + spk + locktime)

        buffer = BytesIO(tx_data)
        tx = TransactionParser.parse_transaction(buffer)

        # For legacy tx, vbytes = size
        expected_size = len(tx_data)
        assert tx.vbytes == expected_size

    def test_parse_transaction_empty_inputs_outputs(self):
        """Test parsing transaction with zero inputs/outputs"""
        version = b'\x01\x00\x00\x00'
        input_count = b'\x00'
        output_count = b'\x00'
        locktime = b'\x00\x00\x00\x00'

        tx_data = version + input_count + output_count + locktime

        buffer = BytesIO(tx_data)
        tx = TransactionParser.parse_transaction(buffer)

        assert len(tx.inputs) == 0
        assert len(tx.outputs) == 0
        assert (tx.witness_flag == 0 or tx.witness_flag == b'\x00')
