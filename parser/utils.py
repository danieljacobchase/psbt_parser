"""
Utility functions for parsing PSBT data
"""

def parse_compact_size(buffer):
    """Parse a Bitcoin compact size (variable-length) integer from a buffer.

    Compact size encoding uses 1, 3, 5, or 9 bytes depending on the value:
    - < 0xfd: 1 byte (the value itself)
    - 0xfd: 1 + 2 bytes (0xfd followed by uint16_le)
    - 0xfe: 1 + 4 bytes (0xfe followed by uint32_le)
    - 0xff: 1 + 8 bytes (0xff followed by uint64_le)

    Args:
        buffer (BytesIO): Buffer containing compact size data.

    Returns:
        tuple[int, int]: A tuple of (value, bytes_consumed) where value is
            the parsed integer and bytes_consumed is the total number of
            bytes read from the buffer.
    """
    byte = buffer.read(1)
    size = byte[0]
    if size < 0xfd:
        return (size, 1)
    elif size == 0xfd:
        value_bytes = buffer.read(2)
        value = int.from_bytes(value_bytes, byteorder='little')
        return (value, 3)
    elif size == 0xfe:
        value_bytes = buffer.read(4)
        value = int.from_bytes(value_bytes, byteorder='little')
        return (value, 5)
    else:
        value_bytes = buffer.read(8)
        value = int.from_bytes(value_bytes, byteorder='little')
        return (value, 9)

def peek_byte(buffer):
    """Preview the next byte without consuming it from the buffer.

    Reads one byte ahead and then resets the buffer position to its
    original location, allowing non-destructive lookahead.

    Args:
        buffer (BytesIO): Buffer to peek into.

    Returns:
        bytes: The next byte in the buffer without advancing the position.
    """
    current_pos = buffer.tell()
    next_byte = buffer.read(1)
    buffer.seek(current_pos)
    return next_byte

def print_bytes(bytes):
    """Print bytes as a hexadecimal string.

    Args:
        bytes (bytes): Byte data to display in hex format.
    """
    print(bytes.hex())
