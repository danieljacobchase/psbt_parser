"""
Unit tests for parser/psbt_parser.py
"""
import pytest
from io import BytesIO
from parser.psbt_parser import PSBTParser
from models.psbt import PSBTMapType, PSBTKey, PSBTVal, PSBTKeyVal, PSBTMap
from models.constants import (
    PSBT_GLOBAL_UNSIGNED_TX,
    PSBT_GLOBAL_TX_VERSION,
    PSBT_GLOBAL_INPUT_COUNT,
    PSBT_GLOBAL_OUTPUT_COUNT
)


class TestParseVal:
    """Test parse_val function"""

    def test_parse_val_empty(self):
        """Test parsing empty value"""
        buffer = BytesIO(b'\x00')
        val = PSBTParser.parse_val(buffer)

        assert val.val_len == 0
        assert val.val_data == b''

    def test_parse_val_single_byte(self):
        """Test parsing single byte value"""
        buffer = BytesIO(b'\x01\x42')
        val = PSBTParser.parse_val(buffer)

        assert val.val_len == 1
        assert val.val_data == b'\x42'

    def test_parse_val_multiple_bytes(self):
        """Test parsing multi-byte value"""
        data = b'\xaa\xbb\xcc\xdd'
        buffer = BytesIO(bytes([len(data)]) + data)
        val = PSBTParser.parse_val(buffer)

        assert val.val_len == 4
        assert val.val_data == data

    def test_parse_val_large_value(self):
        """Test parsing large value with compact size"""
        data = b'\xff' * 300
        # Compact size for 300: 0xfd 0x2c 0x01 (little-endian uint16)
        buffer = BytesIO(b'\xfd\x2c\x01' + data)
        val = PSBTParser.parse_val(buffer)

        assert val.val_len == 300
        assert len(val.val_data) == 300

    def test_parse_val_buffer_position(self):
        """Test that buffer position advances correctly"""
        buffer = BytesIO(b'\x02\xaa\xbb\xff')
        val = PSBTParser.parse_val(buffer)

        assert val.val_len == 2
        assert buffer.read(1) == b'\xff'


class TestParseKey:
    """Test parse_key function"""

    def test_parse_key_no_data(self):
        """Test parsing key with no additional data"""
        # Key length 1, key type 0x00
        buffer = BytesIO(b'\x01\x00')
        key = PSBTParser.parse_key(buffer, PSBTMapType.GLOBAL)

        assert key.key_len == 1
        assert key.key_type == 0x00
        assert key.key_data == b''
        assert key.map_type == PSBTMapType.GLOBAL

    def test_parse_key_with_data(self):
        """Test parsing key with additional data"""
        # Key length 5, key type 0x01, data 0xaabbccdd
        buffer = BytesIO(b'\x05\x01\xaa\xbb\xcc\xdd')
        key = PSBTParser.parse_key(buffer, PSBTMapType.INPUT)

        assert key.key_len == 5
        assert key.key_type == 0x01
        assert key.key_data == b'\xaa\xbb\xcc\xdd'
        assert key.map_type == PSBTMapType.INPUT

    def test_parse_key_global_unsigned_tx(self):
        """Test parsing PSBT_GLOBAL_UNSIGNED_TX key"""
        buffer = BytesIO(b'\x01\x00')
        key = PSBTParser.parse_key(buffer, PSBTMapType.GLOBAL)

        assert key.key_type == PSBT_GLOBAL_UNSIGNED_TX
        assert key.key_data == b''

    def test_parse_key_with_pubkey_data(self):
        """Test parsing key with public key data (33 bytes)"""
        pubkey = b'\x02' + b'\x12' * 32  # Compressed pubkey
        # Key length 34 (1 for type + 33 for pubkey), key type 0x06
        buffer = BytesIO(b'\x22\x06' + pubkey)
        key = PSBTParser.parse_key(buffer, PSBTMapType.OUTPUT)

        assert key.key_len == 34
        assert key.key_type == 0x06
        assert key.key_data == pubkey
        assert key.map_type == PSBTMapType.OUTPUT

    def test_parse_key_buffer_position(self):
        """Test that buffer position advances correctly"""
        buffer = BytesIO(b'\x03\x01\xaa\xbb\xff')
        key = PSBTParser.parse_key(buffer, PSBTMapType.INPUT)

        assert key.key_len == 3
        assert buffer.read(1) == b'\xff'


class TestParseKeyVal:
    """Test parse_key_val function"""

    def test_parse_key_val_empty_value(self):
        """Test parsing key-value pair with empty value"""
        # Key: length 1, type 0
        # Val: length 0
        buffer = BytesIO(b'\x01\x00\x00')
        key_val = PSBTParser.parse_key_val(buffer, PSBTMapType.GLOBAL)

        assert key_val.key.key_type == 0x00
        assert key_val.val.val_len == 0

    def test_parse_key_val_with_data(self):
        """Test parsing key-value pair with data"""
        # Key: length 2, type 1, data 0xaa
        # Val: length 3, data 0xbbccdd
        buffer = BytesIO(b'\x02\x01\xaa\x03\xbb\xcc\xdd')
        key_val = PSBTParser.parse_key_val(buffer, PSBTMapType.INPUT)

        assert key_val.key.key_len == 2
        assert key_val.key.key_type == 0x01
        assert key_val.key.key_data == b'\xaa'
        assert key_val.val.val_len == 3
        assert key_val.val.val_data == b'\xbb\xcc\xdd'

    def test_parse_key_val_transaction_data(self):
        """Test parsing key-value with transaction data"""
        # Simplified transaction data
        tx_data = b'\x01\x00\x00\x00' + b'\x00' * 10
        # Key: PSBT_GLOBAL_UNSIGNED_TX
        # Val: transaction data
        buffer = BytesIO(b'\x01\x00' + bytes([len(tx_data)]) + tx_data)
        key_val = PSBTParser.parse_key_val(buffer, PSBTMapType.GLOBAL)

        assert key_val.key.key_type == PSBT_GLOBAL_UNSIGNED_TX
        assert len(key_val.val.val_data) == len(tx_data)


class TestParseMap:
    """Test parse_map function"""

    def test_parse_map_empty(self):
        """Test parsing empty map"""
        # Just terminator
        buffer = BytesIO(b'\x00')
        psbt_map = PSBTParser.parse_map(buffer, PSBTMapType.GLOBAL)

        assert len(psbt_map.map) == 0

    def test_parse_map_single_entry(self):
        """Test parsing map with single entry"""
        # Key: length 1, type 0
        # Val: length 2, data 0xaabb
        # Terminator: 0x00
        buffer = BytesIO(b'\x01\x00\x02\xaa\xbb\x00')
        psbt_map = PSBTParser.parse_map(buffer, PSBTMapType.GLOBAL)

        assert len(psbt_map.map) == 1
        assert psbt_map.map[0].key.key_type == 0x00
        assert psbt_map.map[0].val.val_data == b'\xaa\xbb'

    def test_parse_map_multiple_entries(self):
        """Test parsing map with multiple entries"""
        # Entry 1: Key(1, 0x00), Val(1, 0xaa)
        # Entry 2: Key(1, 0x01), Val(1, 0xbb)
        # Entry 3: Key(1, 0x02), Val(1, 0xcc)
        # Terminator
        buffer = BytesIO(b'\x01\x00\x01\xaa\x01\x01\x01\xbb\x01\x02\x01\xcc\x00')
        psbt_map = PSBTParser.parse_map(buffer, PSBTMapType.INPUT)

        assert len(psbt_map.map) == 3
        assert psbt_map.map[0].key.key_type == 0x00
        assert psbt_map.map[1].key.key_type == 0x01
        assert psbt_map.map[2].key.key_type == 0x02

    def test_parse_map_buffer_position(self):
        """Test that buffer consumes terminator"""
        buffer = BytesIO(b'\x01\x00\x01\xaa\x00\xff')
        psbt_map = PSBTParser.parse_map(buffer, PSBTMapType.OUTPUT)

        # Should consume up to and including terminator
        assert buffer.read(1) == b'\xff'

    def test_parse_map_global_type(self):
        """Test parsing GLOBAL map type"""
        buffer = BytesIO(b'\x01\x00\x04\x01\x02\x03\x04\x00')
        psbt_map = PSBTParser.parse_map(buffer, PSBTMapType.GLOBAL)

        assert psbt_map.map[0].key.map_type == PSBTMapType.GLOBAL

    def test_parse_map_input_type(self):
        """Test parsing INPUT map type"""
        buffer = BytesIO(b'\x01\x01\x02\xaa\xbb\x00')
        psbt_map = PSBTParser.parse_map(buffer, PSBTMapType.INPUT)

        assert psbt_map.map[0].key.map_type == PSBTMapType.INPUT

    def test_parse_map_output_type(self):
        """Test parsing OUTPUT map type"""
        buffer = BytesIO(b'\x01\x02\x01\xcc\x00')
        psbt_map = PSBTParser.parse_map(buffer, PSBTMapType.OUTPUT)

        assert psbt_map.map[0].key.map_type == PSBTMapType.OUTPUT


class TestParsePsbt:
    """Test parse_psbt function"""

    def test_parse_psbt_invalid_magic_bytes(self):
        """Test that invalid magic bytes raise ValueError"""
        buffer = BytesIO(b'xxxx\xff')
        with pytest.raises(ValueError, match="Invalid magic bytes"):
            PSBTParser.parse_psbt(buffer)

    def test_parse_psbt_invalid_separator(self):
        """Test that invalid separator raises ValueError"""
        buffer = BytesIO(b'psbt\x00')
        with pytest.raises(ValueError, match="Invalid separator"):
            PSBTParser.parse_psbt(buffer)

    def test_parse_psbt_v0_minimal(self):
        """Test parsing minimal PSBT v0"""
        # Magic bytes + separator
        magic = b'psbt\xff'
        # Global map: PSBT_GLOBAL_UNSIGNED_TX key with minimal valid tx (1 input, 1 output)
        minimal_tx = (b'\x01\x00\x00\x00' +  # version
                      b'\x01' + b'\xaa' * 32 + b'\x00\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff' +  # 1 input
                      b'\x01' + (1000).to_bytes(8, 'little') + b'\x01\x00' +  # 1 output with 1-byte script
                      b'\x00\x00\x00\x00')  # locktime
        global_map = b'\x01\x00' + bytes([len(minimal_tx)]) + minimal_tx + b'\x00'
        # 1 input map and 1 output map (both empty)
        input_map = b'\x00'
        output_map = b'\x00'

        buffer = BytesIO(magic + global_map + input_map + output_map)
        psbt = PSBTParser.parse_psbt(buffer)

        assert psbt.version == 0
        assert len(psbt.input_maps) == 1
        assert len(psbt.output_maps) == 1

    def test_parse_psbt_v2_minimal(self):
        """Test parsing minimal PSBT v2"""
        magic = b'psbt\xff'
        # Global map: PSBT_GLOBAL_TX_VERSION (0x02) with value 2
        # Plus PSBT_GLOBAL_INPUT_COUNT and PSBT_GLOBAL_OUTPUT_COUNT both 0
        global_map = (
            b'\x01\x02' + b'\x01\x02' +  # TX_VERSION = 2
            b'\x01\x04' + b'\x01\x00' +  # INPUT_COUNT = 0
            b'\x01\x05' + b'\x01\x00' +  # OUTPUT_COUNT = 0
            b'\x00'  # terminator
        )

        buffer = BytesIO(magic + global_map)
        psbt = PSBTParser.parse_psbt(buffer)

        assert psbt.version == 2
        assert len(psbt.input_maps) == 0
        assert len(psbt.output_maps) == 0

    def test_parse_psbt_v0_with_inputs_outputs(self):
        """Test parsing PSBT v0 with inputs and outputs"""
        magic = b'psbt\xff'
        # Transaction with 1 input and 1 output
        # Version
        tx = b'\x01\x00\x00\x00'
        # 1 input
        tx += b'\x01' + b'\xaa' * 32 + b'\x00\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff'
        # 1 output
        tx += b'\x01' + (50000).to_bytes(8, 'little') + b'\x16' + b'\x00\x14' + b'\xbb' * 20
        # Locktime
        tx += b'\x00\x00\x00\x00'

        global_map = b'\x01\x00' + bytes([len(tx)]) + tx + b'\x00'
        # 1 input map (empty)
        input_map = b'\x00'
        # 1 output map (empty)
        output_map = b'\x00'

        buffer = BytesIO(magic + global_map + input_map + output_map)
        psbt = PSBTParser.parse_psbt(buffer)

        assert psbt.version == 0
        assert len(psbt.input_maps) == 1
        assert len(psbt.output_maps) == 1

    def test_parse_psbt_v2_with_inputs_outputs(self):
        """Test parsing PSBT v2 with inputs and outputs"""
        magic = b'psbt\xff'
        # Global map with counts
        global_map = (
            b'\x01\x02' + b'\x01\x02' +  # TX_VERSION = 2
            b'\x01\x04' + b'\x01\x02' +  # INPUT_COUNT = 2
            b'\x01\x05' + b'\x01\x01' +  # OUTPUT_COUNT = 1
            b'\x00'
        )
        # 2 input maps (empty)
        input_maps = b'\x00\x00'
        # 1 output map (empty)
        output_maps = b'\x00'

        buffer = BytesIO(magic + global_map + input_maps + output_maps)
        psbt = PSBTParser.parse_psbt(buffer)

        assert psbt.version == 2
        assert len(psbt.input_maps) == 2
        assert len(psbt.output_maps) == 1

    def test_parse_psbt_no_version_indicator(self):
        """Test that PSBT without version indicator raises ValueError"""
        magic = b'psbt\xff'
        # Global map with unknown key types (no UNSIGNED_TX or TX_VERSION)
        global_map = b'\x01\x99\x01\xaa\x00'

        buffer = BytesIO(magic + global_map)
        with pytest.raises(ValueError, match="PSBT version could not be determined"):
            PSBTParser.parse_psbt(buffer)

    def test_parse_psbt_v2_creator_stage(self):
        """Test parsing PSBT v2 at creator stage (no input/output counts)"""
        magic = b'psbt\xff'
        # Global map with only TX_VERSION (creator stage may not have counts yet)
        global_map = b'\x01\x02' + b'\x01\x02' + b'\x00'

        buffer = BytesIO(magic + global_map)
        psbt = PSBTParser.parse_psbt(buffer)

        assert psbt.version == 2
        # Should default to 0 inputs and 0 outputs
        assert len(psbt.input_maps) == 0
        assert len(psbt.output_maps) == 0

    def test_parse_psbt_input_map_with_data(self):
        """Test parsing PSBT with non-empty input map"""
        magic = b'psbt\xff'
        # Minimal v0 transaction with 1 input
        tx = (b'\x01\x00\x00\x00' +  # version
              b'\x01' + b'\xcc' * 32 + b'\x00\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff' +  # input
              b'\x00' +  # 0 outputs
              b'\x00\x00\x00\x00')  # locktime
        global_map = b'\x01\x00' + bytes([len(tx)]) + tx + b'\x00'
        # Input map with one key-value pair
        input_map = b'\x01\x01\x02\xaa\xbb\x00'

        buffer = BytesIO(magic + global_map + input_map)
        psbt = PSBTParser.parse_psbt(buffer)

        assert len(psbt.input_maps) == 1
        assert len(psbt.input_maps[0].map) == 1
        assert psbt.input_maps[0].map[0].key.key_type == 0x01

    def test_parse_psbt_output_map_with_data(self):
        """Test parsing PSBT with non-empty output map"""
        magic = b'psbt\xff'
        # Minimal v0 transaction with 1 input and 1 output (can't have 0 inputs - conflicts with SegWit marker)
        tx = (b'\x01\x00\x00\x00' +  # version
              b'\x01' + b'\xaa' * 32 + b'\x00\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff' +  # 1 input
              b'\x01' + (10000).to_bytes(8, 'little') + b'\x02\xaa\xbb' +  # 1 output with 2-byte script
              b'\x00\x00\x00\x00')  # locktime
        global_map = b'\x01\x00' + bytes([len(tx)]) + tx + b'\x00'
        # Input map (empty)
        input_map = b'\x00'
        # Output map with some data
        output_map = b'\x01\x02\x04\x11\x22\x33\x44\x00'

        buffer = BytesIO(magic + global_map + input_map + output_map)
        psbt = PSBTParser.parse_psbt(buffer)

        assert len(psbt.input_maps) == 1
        assert len(psbt.output_maps) == 1
        assert len(psbt.output_maps[0].map) == 1
