"""
Unit tests for parser/psbt_key_parser.py
"""
import pytest
from io import BytesIO
from parser.psbt_key_parser import PSBTKeyParser
from models.keys import PsbtKeyInWitnessUTXO, PsbtKeyOutBIP32Derivation


class TestParseKeyPsbtInWitnessUtxo:
    """Test parse_key_PSBT_IN_WITNESS_UTXO function"""

    def test_parse_witness_utxo_p2wpkh(self):
        """Test parsing witness UTXO for P2WPKH"""
        amount = 100000000  # 1 BTC in satoshis
        amount_bytes = amount.to_bytes(8, byteorder='little')
        # P2WPKH script: OP_0 OP_PUSHBYTES_20 <20 bytes>
        script = b'\x00\x14' + b'\xaa' * 20
        script_len = bytes([len(script)])

        data = amount_bytes + script_len + script
        result = PSBTKeyParser.parse_key_PSBT_IN_WITNESS_UTXO(data)

        assert isinstance(result, PsbtKeyInWitnessUTXO)
        assert result.amount == amount
        assert result.script_hash == script.hex()

    def test_parse_witness_utxo_p2wsh(self):
        """Test parsing witness UTXO for P2WSH"""
        amount = 50000000
        amount_bytes = amount.to_bytes(8, byteorder='little')
        # P2WSH script: OP_0 OP_PUSHBYTES_32 <32 bytes>
        script = b'\x00\x20' + b'\xbb' * 32
        script_len = bytes([len(script)])

        data = amount_bytes + script_len + script
        result = PSBTKeyParser.parse_key_PSBT_IN_WITNESS_UTXO(data)

        assert result.amount == amount
        assert result.script_hash == script.hex()
        assert len(bytes.fromhex(result.script_hash)) == 34

    def test_parse_witness_utxo_zero_amount(self):
        """Test parsing witness UTXO with zero amount"""
        amount_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        script = b'\x00\x14' + b'\x00' * 20
        script_len = bytes([len(script)])

        data = amount_bytes + script_len + script
        result = PSBTKeyParser.parse_key_PSBT_IN_WITNESS_UTXO(data)

        assert result.amount == 0
        assert result.script_hash == script.hex()

    def test_parse_witness_utxo_large_amount(self):
        """Test parsing witness UTXO with large amount"""
        amount = 2100000000000000  # 21M BTC
        amount_bytes = amount.to_bytes(8, byteorder='little')
        script = b'\x00\x14' + b'\xff' * 20
        script_len = bytes([len(script)])

        data = amount_bytes + script_len + script
        result = PSBTKeyParser.parse_key_PSBT_IN_WITNESS_UTXO(data)

        assert result.amount == amount


class TestParseKeyPsbtOutBip32Derivation:
    """Test parse_key_PSBT_OUT_BIP32_DERIVATION function"""

    def test_parse_bip32_derivation_receive_address(self):
        """Test parsing BIP32 derivation for receive address (m/84'/0'/0'/0/5)"""
        fingerprint = b'\x12\x34\x56\x78'
        # Path indices: 84', 0', 0', 0, 5
        # Hardened indices have bit 31 set (0x80000000)
        indices_bytes = (
            (84 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0).to_bytes(4, 'little') +
            (5).to_bytes(4, 'little')
        )

        data = fingerprint + indices_bytes
        result = PSBTKeyParser.parse_key_PSBT_OUT_BIP32_DERIVATION(data)

        assert isinstance(result, PsbtKeyOutBIP32Derivation)
        assert result.fingerprint == fingerprint.hex()
        assert result.indices == [84, 0, 0, 0, 5]
        assert result.hardened == [True, True, True, False, False]
        assert result.is_change == False  # Index 3 is 0 (receive)

    def test_parse_bip32_derivation_change_address(self):
        """Test parsing BIP32 derivation for change address (m/84'/0'/0'/1/3)"""
        fingerprint = b'\xaa\xbb\xcc\xdd'
        # Path indices: 84', 0', 0', 1, 3
        indices_bytes = (
            (84 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (1).to_bytes(4, 'little') +
            (3).to_bytes(4, 'little')
        )

        data = fingerprint + indices_bytes
        result = PSBTKeyParser.parse_key_PSBT_OUT_BIP32_DERIVATION(data)

        assert result.fingerprint == fingerprint.hex()
        assert result.indices == [84, 0, 0, 1, 3]
        assert result.hardened == [True, True, True, False, False]
        assert result.is_change == True  # Index 3 is 1 (change)

    def test_parse_bip32_derivation_all_hardened(self):
        """Test parsing BIP32 derivation with all hardened indices"""
        fingerprint = b'\x11\x22\x33\x44'
        # All indices hardened
        indices_bytes = (
            (0 | 0x80000000).to_bytes(4, 'little') +
            (1 | 0x80000000).to_bytes(4, 'little') +
            (2 | 0x80000000).to_bytes(4, 'little') +
            (3 | 0x80000000).to_bytes(4, 'little') +
            (4 | 0x80000000).to_bytes(4, 'little')
        )

        data = fingerprint + indices_bytes
        result = PSBTKeyParser.parse_key_PSBT_OUT_BIP32_DERIVATION(data)

        assert result.indices == [0, 1, 2, 3, 4]
        assert all(result.hardened)  # All should be True

    def test_parse_bip32_derivation_legacy_path(self):
        """Test parsing BIP32 derivation for legacy address (m/44'/0'/0'/0/10)"""
        fingerprint = b'\xff\xee\xdd\xcc'
        # Path indices: 44', 0', 0', 0, 10
        indices_bytes = (
            (44 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0).to_bytes(4, 'little') +
            (10).to_bytes(4, 'little')
        )

        data = fingerprint + indices_bytes
        result = PSBTKeyParser.parse_key_PSBT_OUT_BIP32_DERIVATION(data)

        assert result.indices == [44, 0, 0, 0, 10]
        assert result.hardened == [True, True, True, False, False]
        assert result.is_change == False

    def test_parse_bip32_derivation_testnet(self):
        """Test parsing BIP32 derivation for testnet (m/84'/1'/0'/0/0)"""
        fingerprint = b'\x01\x02\x03\x04'
        # Coin type 1 for testnet
        indices_bytes = (
            (84 | 0x80000000).to_bytes(4, 'little') +
            (1 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0).to_bytes(4, 'little') +
            (0).to_bytes(4, 'little')
        )

        data = fingerprint + indices_bytes
        result = PSBTKeyParser.parse_key_PSBT_OUT_BIP32_DERIVATION(data)

        assert result.indices == [84, 1, 0, 0, 0]
        assert result.indices[1] == 1  # Testnet coin type

    def test_parse_bip32_derivation_high_index(self):
        """Test parsing BIP32 derivation with high index values"""
        fingerprint = b'\xab\xcd\xef\x12'
        # High index value (but not hardened)
        indices_bytes = (
            (84 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0).to_bytes(4, 'little') +
            (1000000).to_bytes(4, 'little')
        )

        data = fingerprint + indices_bytes
        result = PSBTKeyParser.parse_key_PSBT_OUT_BIP32_DERIVATION(data)

        assert result.indices[4] == 1000000
        assert result.hardened[4] == False

    def test_parse_bip32_derivation_fingerprint_format(self):
        """Test that fingerprint is correctly formatted as hex"""
        fingerprint = b'\x12\x34\x56\x78'
        indices_bytes = (
            (84 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0).to_bytes(4, 'little') +
            (0).to_bytes(4, 'little')
        )

        data = fingerprint + indices_bytes
        result = PSBTKeyParser.parse_key_PSBT_OUT_BIP32_DERIVATION(data)

        assert result.fingerprint == '12345678'
        assert len(result.fingerprint) == 8


class TestParseKeyPsbtInNonWitnessUtxo:
    """Test parse_key_PSBT_IN_NON_WITNESS_UTXO function"""

    def test_parse_non_witness_utxo_legacy_tx(self):
        """Test parsing non-witness UTXO (legacy transaction)"""
        # Create a simple legacy transaction
        version = b'\x01\x00\x00\x00'
        input_count = b'\x01'
        txid = b'\xaa' * 32
        vout = b'\x00\x00\x00\x00'
        ss_size = b'\x00'
        seq = b'\xff\xff\xff\xff'
        output_count = b'\x01'
        amount = (50000).to_bytes(8, 'little')
        spk_size = b'\x19'
        spk = b'\x76\xa9\x14' + b'\xbb' * 20 + b'\x88\xac'
        locktime = b'\x00\x00\x00\x00'

        tx_data = (version + input_count + txid + vout + ss_size + seq +
                   output_count + amount + spk_size + spk + locktime)

        result = PSBTKeyParser.parse_key_PSBT_IN_NON_WITNESS_UTXO(tx_data)

        assert result is not None
        assert result.version == version
        assert len(result.inputs) == 1
        assert len(result.outputs) == 1

    def test_parse_non_witness_utxo_multiple_outputs(self):
        """Test parsing non-witness UTXO with multiple outputs"""
        version = b'\x01\x00\x00\x00'
        input_count = b'\x01'
        input_data = b'\xcc' * 32 + b'\x00\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff'
        output_count = b'\x02'
        output1 = (30000).to_bytes(8, 'little') + b'\x19' + b'\x76\xa9\x14' + b'\x11' * 20 + b'\x88\xac'
        output2 = (20000).to_bytes(8, 'little') + b'\x16' + b'\x00\x14' + b'\x22' * 20
        locktime = b'\x00\x00\x00\x00'

        tx_data = version + input_count + input_data + output_count + output1 + output2 + locktime

        result = PSBTKeyParser.parse_key_PSBT_IN_NON_WITNESS_UTXO(tx_data)

        assert len(result.outputs) == 2
        assert result.outputs[0].amount == 30000
        assert result.outputs[1].amount == 20000


class TestParseKeyPsbtInPreviousTxid:
    """Test parse_key_PSBT_IN_PREVIOUS_TXID function"""

    def test_parse_previous_txid(self):
        """Test parsing previous TXID"""
        txid = b'\x12\x34\x56\x78' * 8  # 32 bytes
        result = PSBTKeyParser.parse_key_PSBT_IN_PREVIOUS_TXID(txid)

        assert result == txid
        assert len(result) == 32

    def test_parse_previous_txid_all_zeros(self):
        """Test parsing TXID with all zeros"""
        txid = b'\x00' * 32
        result = PSBTKeyParser.parse_key_PSBT_IN_PREVIOUS_TXID(txid)

        assert result == txid

    def test_parse_previous_txid_all_ones(self):
        """Test parsing TXID with all 0xff"""
        txid = b'\xff' * 32
        result = PSBTKeyParser.parse_key_PSBT_IN_PREVIOUS_TXID(txid)

        assert result == txid


class TestParseKeyPsbtInOutputIndex:
    """Test parse_key_PSBT_IN_OUTPUT_INDEX function"""

    def test_parse_output_index_zero(self):
        """Test parsing output index 0"""
        data = (0).to_bytes(4, byteorder='little')
        result = PSBTKeyParser.parse_key_PSBT_IN_OUTPUT_INDEX(data)

        assert result == 0

    def test_parse_output_index_one(self):
        """Test parsing output index 1"""
        data = (1).to_bytes(4, byteorder='little')
        result = PSBTKeyParser.parse_key_PSBT_IN_OUTPUT_INDEX(data)

        assert result == 1

    def test_parse_output_index_large(self):
        """Test parsing large output index"""
        data = (12345).to_bytes(4, byteorder='little')
        result = PSBTKeyParser.parse_key_PSBT_IN_OUTPUT_INDEX(data)

        assert result == 12345

    def test_parse_output_index_max_uint32(self):
        """Test parsing maximum uint32 output index"""
        data = (4294967295).to_bytes(4, byteorder='little')
        result = PSBTKeyParser.parse_key_PSBT_IN_OUTPUT_INDEX(data)

        assert result == 4294967295


class TestParseKeyPsbtOutAmount:
    """Test parse_key_PSBT_OUT_AMOUNT function"""

    def test_parse_out_amount_zero(self):
        """Test parsing zero amount"""
        data = (0).to_bytes(8, byteorder='little')
        result = PSBTKeyParser.parse_key_PSBT_OUT_AMOUNT(data)

        assert result == 0

    def test_parse_out_amount_small(self):
        """Test parsing small amount"""
        amount = 1000  # 1000 satoshis
        data = amount.to_bytes(8, byteorder='little')
        result = PSBTKeyParser.parse_key_PSBT_OUT_AMOUNT(data)

        assert result == amount

    def test_parse_out_amount_one_btc(self):
        """Test parsing 1 BTC amount"""
        amount = 100000000  # 1 BTC
        data = amount.to_bytes(8, byteorder='little')
        result = PSBTKeyParser.parse_key_PSBT_OUT_AMOUNT(data)

        assert result == amount

    def test_parse_out_amount_21m_btc(self):
        """Test parsing 21M BTC amount"""
        amount = 2100000000000000  # 21M BTC
        data = amount.to_bytes(8, byteorder='little')
        result = PSBTKeyParser.parse_key_PSBT_OUT_AMOUNT(data)

        assert result == amount

    def test_parse_out_amount_max_uint64(self):
        """Test parsing maximum uint64 amount"""
        amount = 18446744073709551615  # Max uint64
        data = amount.to_bytes(8, byteorder='little')
        result = PSBTKeyParser.parse_key_PSBT_OUT_AMOUNT(data)

        assert result == amount


class TestParseKeyPsbtOutScript:
    """Test parse_key_PSBT_OUT_SCRIPT function"""

    def test_parse_out_script_p2pkh(self):
        """Test parsing P2PKH script"""
        # P2PKH: OP_DUP OP_HASH160 <20 bytes> OP_EQUALVERIFY OP_CHECKSIG
        script = b'\x76\xa9\x14' + b'\xaa' * 20 + b'\x88\xac'
        result = PSBTKeyParser.parse_key_PSBT_OUT_SCRIPT(script)

        assert result == script
        assert len(result) == 25

    def test_parse_out_script_p2wpkh(self):
        """Test parsing P2WPKH script"""
        # P2WPKH: OP_0 <20 bytes>
        script = b'\x00\x14' + b'\xbb' * 20
        result = PSBTKeyParser.parse_key_PSBT_OUT_SCRIPT(script)

        assert result == script
        assert len(result) == 22

    def test_parse_out_script_p2sh(self):
        """Test parsing P2SH script"""
        # P2SH: OP_HASH160 <20 bytes> OP_EQUAL
        script = b'\xa9\x14' + b'\xcc' * 20 + b'\x87'
        result = PSBTKeyParser.parse_key_PSBT_OUT_SCRIPT(script)

        assert result == script
        assert len(result) == 23

    def test_parse_out_script_p2wsh(self):
        """Test parsing P2WSH script"""
        # P2WSH: OP_0 <32 bytes>
        script = b'\x00\x20' + b'\xdd' * 32
        result = PSBTKeyParser.parse_key_PSBT_OUT_SCRIPT(script)

        assert result == script
        assert len(result) == 34

    def test_parse_out_script_p2tr(self):
        """Test parsing P2TR (Taproot) script"""
        # P2TR: OP_1 <32 bytes>
        script = b'\x51\x20' + b'\xee' * 32
        result = PSBTKeyParser.parse_key_PSBT_OUT_SCRIPT(script)

        assert result == script
        assert len(result) == 34

    def test_parse_out_script_empty(self):
        """Test parsing empty script"""
        script = b''
        result = PSBTKeyParser.parse_key_PSBT_OUT_SCRIPT(script)

        assert result == b''

    def test_parse_out_script_op_return(self):
        """Test parsing OP_RETURN script"""
        # OP_RETURN <data>
        script = b'\x6a\x0cHello World!'
        result = PSBTKeyParser.parse_key_PSBT_OUT_SCRIPT(script)

        assert result == script
