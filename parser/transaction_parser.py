"""
Bitcoin transaction parsing functions
"""
from models.transaction import Transaction, TXInput, TXOutput, TXWitnessStack, TXWitnessStackItem
from .utils import parse_compact_size, peek_byte

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
    version = buffer.read(4)
    is_segwit = False
    witness_flag = 0
    if peek_byte(buffer) == b'\x00': # segwit transaction
        is_segwit = True
        witness_flag = buffer.read(1) # consume the 0x00 byte
    input_ct, _ = parse_compact_size(buffer)
    inputs = [parse_input(buffer) for _ in range(input_ct)]
    output_ct, _ = parse_compact_size(buffer)
    outputs = [parse_output(buffer) for _ in range(output_ct)]
    witness_stacks = []
    if is_segwit:
        witness_stacks.append(parse_witness(buffer, input_ct))
    locktime = buffer.read(4)
    return Transaction(version, witness_flag, inputs, outputs, witness_stacks, locktime)

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
    return TXInput(txid, vout, ss_size, ss, seq)

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
    return TXOutput(amount, spk_size, spk)

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
            stack_item = TXWitnessStackItem(stack_item_size, stack_item_data)
            stack_items.append(stack_item)
        witness_stack = TXWitnessStack(stack_items)
        witness_stacks.append(witness_stack)
    return witness_stacks
