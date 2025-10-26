"""
Bitcoin transaction parsing functions
"""
from models.transaction import Transaction, TXInput, TXOutput, TXWitnessStack, TXWitnessStackItem
from .parser_utils import parse_compact_size, peek_byte, get_remaining_bytes


class TransactionParser:
    """Parser for Bitcoin transactions."""

    @staticmethod
    def parse_transaction(buffer):
        """Parse a Bitcoin transaction from a buffer.

        Supports both legacy and SegWit transaction formats. Detects
        SegWit transactions by checking for the witness flag and parses
        witness data accordingly.

        Args:
            buffer (BytesIO): Buffer containing raw transaction data.

        Returns:
            Transaction: A parsed transaction object with version, inputs,
                outputs, witness data (if SegWit), and locktime.
        """
        # Get the size of the transaction data
        tx_size = len(buffer.getvalue())

        version = buffer.read(4)
        is_segwit = False
        witness_flag = 0

        # Check if transaction is SegWit
        if peek_byte(buffer) == b'\x00': # segwit transaction
            is_segwit = True
            marker = buffer.read(1) # consume the 0x00 marker byte
            witness_flag = int.from_bytes(buffer.read(1), byteorder='little') # consume the 0x01 flag byte

        # Parse inputs and outputs
        input_ct, _ = parse_compact_size(buffer)
        inputs = [TransactionParser.parse_input(buffer) for _ in range(input_ct)]
        output_ct, _ = parse_compact_size(buffer)
        outputs = [TransactionParser.parse_output(buffer) for _ in range(output_ct)]

        # Parse witness data (if present)
        witness_stacks = []
        witness_size = 0
        if is_segwit:
            witness_size = get_remaining_bytes(buffer) - 4  # Minus 4 bytes for locktime
            witness_stacks.append(TransactionParser.parse_witness(buffer, input_ct))

        # Read locktime
        locktime = buffer.read(4)

        # Calculate weight and vbytes
        weight = (tx_size * 4) + witness_size
        vbytes = weight / 4

        return Transaction(version=version, witness_flag=witness_flag, inputs=inputs, outputs=outputs, witness=witness_stacks, locktime=locktime, vbytes=vbytes)

    @staticmethod
    def parse_input(buffer):
        """Parse a single transaction input from a buffer.

        Reads the previous transaction ID, output index, scriptSig,
        and sequence number.

        Args:
            buffer (BytesIO): Buffer containing transaction input data.

        Returns:
            TXInput: A transaction input object with txid, vout, scriptSig,
                and sequence fields.
        """
        txid = buffer.read(32)
        vout = buffer.read(4)
        ss_size, _ = parse_compact_size(buffer)
        ss = buffer.read(ss_size)
        seq = buffer.read(4)
        return TXInput(txid=txid, vout=vout, ss_size=ss_size, ss=ss, seq=seq)

    @staticmethod
    def parse_output(buffer):
        """Parse a single transaction output from a buffer.

        Reads the output amount in satoshis and the scriptPubKey.

        Args:
            buffer (BytesIO): Buffer containing transaction output data.

        Returns:
            TXOutput: A transaction output object with amount and
                scriptPubKey fields.
        """
        amount_bytes = buffer.read(8)
        amount = int.from_bytes(amount_bytes, byteorder='little')
        spk_size, _ = parse_compact_size(buffer)
        spk = buffer.read(spk_size)
        return TXOutput(amount=amount, spk_size=spk_size, spk=spk)

    @staticmethod
    def parse_witness(buffer, input_count):
        """Parse witness data for a SegWit transaction.

        Reads witness stack data for each input in the transaction.
        Each witness stack contains a variable number of stack items.

        Args:
            buffer (BytesIO): Buffer containing witness data.
            input_count (int): Number of inputs in the transaction.

        Returns:
            list[TXWitnessStack]: List of witness stacks, one per input.
        """
        witness_stacks = []
        for i in range(input_count):
            stack_item_count, _ = parse_compact_size(buffer)
            stack_items = []
            for j in range(stack_item_count):
                stack_item_size, _ = parse_compact_size(buffer)
                stack_item_data = buffer.read(stack_item_size)
                stack_item = TXWitnessStackItem(stack_item_size=stack_item_size, stack_item=stack_item_data)
                stack_items.append(stack_item)
            witness_stack = TXWitnessStack(witness_items=stack_items)
            witness_stacks.append(witness_stack)
        return witness_stacks
