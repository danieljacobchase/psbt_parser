"""
PSBT parsing functions
"""
from io import BytesIO
from models.psbt import *
from models.constants import PSBT_GLOBAL_UNSIGNED_TX, PSBT_GLOBAL_INPUT_COUNT, PSBT_GLOBAL_OUTPUT_COUNT, PSBT_GLOBAL_TX_VERSION
from .transaction_parser import TransactionParser
from .utils import parse_compact_size, peek_byte

class PSBTParser:
    """Parser for Partially Signed Bitcoin Transactions."""

    @staticmethod
    def parse_psbt(buffer):
        """Parse a Partially Signed Bitcoin Transaction from a buffer.

        Reads and validates the PSBT magic bytes, determines the version,
        and parses the global map, input maps, and output maps according
        to BIP-174 and BIP-370 specifications.

        Args:
            buffer (BytesIO): Buffer containing raw PSBT data.

        Returns:
            PSBT: A parsed PSBT object containing version, global map,
                input maps, and output maps.

        Raises:
            ValueError: If magic bytes are invalid, separator is invalid,
                or PSBT version cannot be determined.
        """
        # Parse and validate magic bytes and separator
        magic_bytes = buffer.read(4)
        separator = buffer.read(1)
        if magic_bytes != b'psbt':
            raise ValueError(f"Invalid magic bytes: {magic_bytes.hex()}")
        if separator != b'\xff':
            raise ValueError(f"Invalid separator: {separator.hex()}")

        # Parse global map
        global_map = PSBTParser.parse_map(buffer, PSBTMapType.GLOBAL)

        # Determine PSBT version
        psbt_version = -1
        for key_val in global_map.map:
            if key_val.key.key_type == PSBT_GLOBAL_UNSIGNED_TX:
                psbt_version = 0
                break
            if key_val.key.key_type == PSBT_GLOBAL_TX_VERSION:
                psbt_version = 2
                break
        if psbt_version == -1:
            raise ValueError("PSBT version could not be determined; global map parsed incorrectly")

        # Determine number of inputs and outputs
        if psbt_version == PSBT_GLOBAL_UNSIGNED_TX: # parse transaction to determine input and output counts
            # Parse transaction
            transaction_buffer = BytesIO(global_map.map[0].val.val_data)
            transaction = TransactionParser.parse_transaction(transaction_buffer)
            input_ct = transaction.get_input_count()
            output_ct = transaction.get_output_count()
        else: # search for type keys 04 and 05 in global map, which are input and output counts, respectively
            for key_val in global_map.map:
                if key_val.key.key_type == PSBT_GLOBAL_INPUT_COUNT:
                    input_ct = key_val.val.val_data
                if key_val.key.key_type == PSBT_GLOBAL_OUTPUT_COUNT:
                    output_ct = key_val.val.val_data

        # Parse input maps
        input_maps = [PSBTParser.parse_map(buffer, PSBTMapType.INPUT) for _ in range(input_ct)]

        # Parse output maps
        output_maps = [PSBTParser.parse_map(buffer, PSBTMapType.OUTPUT) for _ in range(output_ct)]

        return PSBT(psbt_version, global_map, input_maps, output_maps)

    @staticmethod
    def parse_map(buffer, map_type: PSBTMapType):
        """Parse a PSBT map of key-value pairs from a buffer.

        Reads key-value pairs until a 0x00 terminator byte is encountered.
        Maps are used for global data, per-input data, and per-output data
        in PSBT format.

        Args:
            buffer (BytesIO): Buffer containing PSBT map data.
            map_type (PSBTMapType): Type of the map (GLOBAL, INPUT, or OUTPUT).

        Returns:
            PSBTMap: A map object containing the parsed key-value pairs.
        """
        map = []
        while peek_byte(buffer) != b'\x00':
            key_val = PSBTParser.parse_key_val(buffer, map_type)
            map.append(key_val)
        buffer.read(1) # consume the 0x00 byte
        return PSBTMap(map)

    @staticmethod
    def parse_key_val(buffer, map_type: PSBTMapType):
        """Parse a single PSBT key-value pair from a buffer.

        Args:
            buffer (BytesIO): Buffer containing key-value pair data.
            map_type (PSBTMapType): Type of the map (GLOBAL, INPUT, or OUTPUT).

        Returns:
            PSBTKeyVal: A key-value pair object containing the parsed key and value.
        """
        key = PSBTParser.parse_key(buffer, map_type)
        val = PSBTParser.parse_val(buffer)
        return PSBTKeyVal(key, val)

    @staticmethod
    def parse_key(buffer, map_type: PSBTMapType):
        """Parse a PSBT key from a buffer.

        Reads the key length as a compact size, then the key type and
        any additional key data.

        Args:
            buffer (BytesIO): Buffer containing key data.
            map_type (PSBTMapType): Type of the map (GLOBAL, INPUT, or OUTPUT).

        Returns:
            PSBTKey: A key object containing length, type, and data fields.
        """
        key_len, _ = parse_compact_size(buffer)
        key_type, key_type_len = parse_compact_size(buffer)
        key_data = buffer.read(key_len - key_type_len)
        return PSBTKey(key_len, key_type, key_data, map_type)

    @staticmethod
    def parse_val(buffer):
        """Parse a PSBT value from a buffer.

        Reads the value length as a compact size, then the value data.

        Args:
            buffer (BytesIO): Buffer containing value data.

        Returns:
            PSBTVal: A value object containing length and data fields.
        """
        val_len, _ = parse_compact_size(buffer)
        val_data = buffer.read(val_len)
        return PSBTVal(val_len, val_data)

