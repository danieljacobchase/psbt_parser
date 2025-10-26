"""
Unit tests for parser/parser_utils.py
"""
import pytest
from io import BytesIO
from parser.parser_utils import parse_compact_size, peek_byte, get_remaining_bytes, print_bytes


class TestParseCompactSize:
    """Test parse_compact_size function"""

    def test_single_byte_size_zero(self):
        """Test compact size parsing for value 0"""
        buffer = BytesIO(b'\x00')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 0
        assert bytes_consumed == 1

    def test_single_byte_size_small(self):
        """Test compact size parsing for small values < 0xfd"""
        buffer = BytesIO(b'\x05')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 5
        assert bytes_consumed == 1

    def test_single_byte_size_max(self):
        """Test compact size parsing for max single-byte value (0xfc)"""
        buffer = BytesIO(b'\xfc')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 252
        assert bytes_consumed == 1

    def test_three_byte_size_min(self):
        """Test compact size parsing for 0xfd prefix (3 bytes total)"""
        # 0xfd followed by uint16_le for value 253
        buffer = BytesIO(b'\xfd\xfd\x00')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 253
        assert bytes_consumed == 3

    def test_three_byte_size_large(self):
        """Test compact size parsing for larger 3-byte value"""
        # 0xfd followed by uint16_le for value 65535 (0xffff)
        buffer = BytesIO(b'\xfd\xff\xff')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 65535
        assert bytes_consumed == 3

    def test_five_byte_size_min(self):
        """Test compact size parsing for 0xfe prefix (5 bytes total)"""
        # 0xfe followed by uint32_le for value 65536 (0x00010000)
        buffer = BytesIO(b'\xfe\x00\x00\x01\x00')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 65536
        assert bytes_consumed == 5

    def test_five_byte_size_large(self):
        """Test compact size parsing for large 5-byte value"""
        # 0xfe followed by uint32_le for value 4294967295 (0xffffffff)
        buffer = BytesIO(b'\xfe\xff\xff\xff\xff')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 4294967295
        assert bytes_consumed == 5

    def test_nine_byte_size_min(self):
        """Test compact size parsing for 0xff prefix (9 bytes total)"""
        # 0xff followed by uint64_le for value 4294967296 (0x0000000100000000)
        buffer = BytesIO(b'\xff\x00\x00\x00\x00\x01\x00\x00\x00')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 4294967296
        assert bytes_consumed == 9

    def test_nine_byte_size_large(self):
        """Test compact size parsing for large 9-byte value"""
        # 0xff followed by uint64_le for a large value
        buffer = BytesIO(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 18446744073709551615
        assert bytes_consumed == 9

    def test_buffer_position_advances(self):
        """Test that buffer position advances correctly"""
        buffer = BytesIO(b'\x05\xaa\xbb')
        value, bytes_consumed = parse_compact_size(buffer)
        assert value == 5
        assert buffer.tell() == 1
        # Next bytes should be 0xaa
        assert buffer.read(1) == b'\xaa'


class TestPeekByte:
    """Test peek_byte function"""

    def test_peek_byte_single(self):
        """Test peeking at a single byte"""
        buffer = BytesIO(b'\x42')
        peeked = peek_byte(buffer)
        assert peeked == b'\x42'
        # Verify position hasn't changed
        assert buffer.tell() == 0

    def test_peek_byte_multiple_calls(self):
        """Test that multiple peeks return the same byte"""
        buffer = BytesIO(b'\xff\xaa\xbb')
        peek1 = peek_byte(buffer)
        peek2 = peek_byte(buffer)
        peek3 = peek_byte(buffer)
        assert peek1 == peek2 == peek3 == b'\xff'
        assert buffer.tell() == 0

    def test_peek_byte_after_read(self):
        """Test peeking after reading from buffer"""
        buffer = BytesIO(b'\x01\x02\x03')
        buffer.read(1)  # Consume first byte
        peeked = peek_byte(buffer)
        assert peeked == b'\x02'
        assert buffer.tell() == 1
        # Verify next read gets the same byte
        assert buffer.read(1) == b'\x02'

    def test_peek_byte_preserves_position(self):
        """Test that peek doesn't affect subsequent reads"""
        buffer = BytesIO(b'\xaa\xbb\xcc')
        buffer.read(1)  # Position at 1
        peek_byte(buffer)
        peek_byte(buffer)
        # Next read should still get 0xbb
        assert buffer.read(1) == b'\xbb'
        assert buffer.tell() == 2

    def test_peek_byte_at_end(self):
        """Test peeking at end of buffer"""
        buffer = BytesIO(b'\x01')
        buffer.read(1)  # Move to end
        peeked = peek_byte(buffer)
        assert peeked == b''
        assert buffer.tell() == 1


class TestGetRemainingBytes:
    """Test get_remaining_bytes function"""

    def test_remaining_bytes_full_buffer(self):
        """Test remaining bytes for full buffer"""
        buffer = BytesIO(b'\x01\x02\x03\x04\x05')
        remaining = get_remaining_bytes(buffer)
        assert remaining == 5
        assert buffer.tell() == 0

    def test_remaining_bytes_after_read(self):
        """Test remaining bytes after partial read"""
        buffer = BytesIO(b'\x01\x02\x03\x04\x05')
        buffer.read(2)
        remaining = get_remaining_bytes(buffer)
        assert remaining == 3
        assert buffer.tell() == 2

    def test_remaining_bytes_at_end(self):
        """Test remaining bytes when at end of buffer"""
        buffer = BytesIO(b'\x01\x02\x03')
        buffer.read(3)
        remaining = get_remaining_bytes(buffer)
        assert remaining == 0
        assert buffer.tell() == 3

    def test_remaining_bytes_empty_buffer(self):
        """Test remaining bytes for empty buffer"""
        buffer = BytesIO(b'')
        remaining = get_remaining_bytes(buffer)
        assert remaining == 0

    def test_remaining_bytes_preserves_position(self):
        """Test that get_remaining_bytes preserves buffer position"""
        buffer = BytesIO(b'\x01\x02\x03\x04\x05')
        buffer.read(2)
        original_pos = buffer.tell()
        remaining = get_remaining_bytes(buffer)
        assert buffer.tell() == original_pos
        assert remaining == 3

    def test_remaining_bytes_middle_of_buffer(self):
        """Test remaining bytes from middle of buffer"""
        buffer = BytesIO(b'\x00' * 100)
        buffer.read(50)
        remaining = get_remaining_bytes(buffer)
        assert remaining == 50
        assert buffer.tell() == 50


class TestPrintBytes:
    """Test print_bytes function"""

    def test_print_bytes_simple(self, capsys):
        """Test printing simple byte sequence"""
        test_bytes = b'\x01\x02\x03'
        print_bytes(test_bytes)
        captured = capsys.readouterr()
        assert captured.out.strip() == '010203'

    def test_print_bytes_hex_values(self, capsys):
        """Test printing bytes with various hex values"""
        test_bytes = b'\xff\xaa\xbb\xcc'
        print_bytes(test_bytes)
        captured = capsys.readouterr()
        assert captured.out.strip() == 'ffaabbcc'

    def test_print_bytes_empty(self, capsys):
        """Test printing empty bytes"""
        test_bytes = b''
        print_bytes(test_bytes)
        captured = capsys.readouterr()
        assert captured.out.strip() == ''

    def test_print_bytes_single(self, capsys):
        """Test printing single byte"""
        test_bytes = b'\x42'
        print_bytes(test_bytes)
        captured = capsys.readouterr()
        assert captured.out.strip() == '42'
