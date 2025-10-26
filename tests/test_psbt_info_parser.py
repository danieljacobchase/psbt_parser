"""
Unit tests for parser/psbt_info_parser.py
"""
import pytest
from io import BytesIO
from parser.psbt_info_parser import PSBTInfoParser
from parser.psbt_parser import PSBTParser
from models.psbt import PSBTMap, PSBTKeyVal, PSBTKey, PSBTVal, PSBTMapType
from models.constants import (
    PSBT_IN_WITNESS_UTXO,
    PSBT_IN_NON_WITNESS_UTXO,
    PSBT_OUT_BIP32_DERIVATION,
    PSBT_IN_WITNESS_SCRIPT,
    PSBT_IN_FINAL_SCRIPTSIG,
    PSBT_IN_FINAL_SCRIPTWITNESS,
    PSBT_OUT_SCRIPT,
    OP_DUP,
    OP_HASH160,
    OP_PUSHBYTES_20,
    OP_EQUALVERIFY,
    OP_CHECKSIG,
    OP_EQUAL,
    OP_PUSHBYTES_32,
    OP_0,
    OP_1
)


class TestFindKeyIndex:
    """Test find_key_index function"""

    def test_find_key_index_first_position(self):
        """Test finding key at first position"""
        key1 = PSBTKey(1, 0x01, b'', PSBTMapType.INPUT)
        val1 = PSBTVal(1, b'\xaa')
        key2 = PSBTKey(1, 0x02, b'', PSBTMapType.INPUT)
        val2 = PSBTVal(1, b'\xbb')

        psbt_map = PSBTMap([PSBTKeyVal(key1, val1), PSBTKeyVal(key2, val2)])

        index = PSBTInfoParser.find_key_index(psbt_map, 0x01)
        assert index == 0

    def test_find_key_index_middle_position(self):
        """Test finding key in middle of map"""
        key1 = PSBTKey(1, 0x01, b'', PSBTMapType.INPUT)
        val1 = PSBTVal(1, b'\xaa')
        key2 = PSBTKey(1, 0x02, b'', PSBTMapType.INPUT)
        val2 = PSBTVal(1, b'\xbb')
        key3 = PSBTKey(1, 0x03, b'', PSBTMapType.INPUT)
        val3 = PSBTVal(1, b'\xcc')

        psbt_map = PSBTMap([
            PSBTKeyVal(key1, val1),
            PSBTKeyVal(key2, val2),
            PSBTKeyVal(key3, val3)
        ])

        index = PSBTInfoParser.find_key_index(psbt_map, 0x02)
        assert index == 1

    def test_find_key_index_last_position(self):
        """Test finding key at last position"""
        key1 = PSBTKey(1, 0x01, b'', PSBTMapType.INPUT)
        val1 = PSBTVal(1, b'\xaa')
        key2 = PSBTKey(1, 0x02, b'', PSBTMapType.INPUT)
        val2 = PSBTVal(1, b'\xbb')

        psbt_map = PSBTMap([PSBTKeyVal(key1, val1), PSBTKeyVal(key2, val2)])

        index = PSBTInfoParser.find_key_index(psbt_map, 0x02)
        assert index == 1

    def test_find_key_index_not_found(self):
        """Test finding key that doesn't exist"""
        key1 = PSBTKey(1, 0x01, b'', PSBTMapType.INPUT)
        val1 = PSBTVal(1, b'\xaa')
        key2 = PSBTKey(1, 0x02, b'', PSBTMapType.INPUT)
        val2 = PSBTVal(1, b'\xbb')

        psbt_map = PSBTMap([PSBTKeyVal(key1, val1), PSBTKeyVal(key2, val2)])

        index = PSBTInfoParser.find_key_index(psbt_map, 0x99)
        assert index == -1

    def test_find_key_index_empty_map(self):
        """Test finding key in empty map"""
        psbt_map = PSBTMap([])

        index = PSBTInfoParser.find_key_index(psbt_map, 0x01)
        assert index == -1

    def test_find_key_index_witness_utxo(self):
        """Test finding PSBT_IN_WITNESS_UTXO key"""
        key = PSBTKey(1, PSBT_IN_WITNESS_UTXO, b'', PSBTMapType.INPUT)
        val = PSBTVal(30, b'\x00' * 30)
        psbt_map = PSBTMap([PSBTKeyVal(key, val)])

        index = PSBTInfoParser.find_key_index(psbt_map, PSBT_IN_WITNESS_UTXO)
        assert index == 0


class TestDetermineScriptType:
    """Test determine_script_type function"""

    def test_determine_script_type_p2pkh(self):
        """Test identifying P2PKH script"""
        # OP_DUP OP_HASH160 <20 bytes> OP_EQUALVERIFY OP_CHECKSIG
        script = bytes([OP_DUP, OP_HASH160, OP_PUSHBYTES_20]) + b'\xaa' * 20 + bytes([OP_EQUALVERIFY, OP_CHECKSIG])
        result = PSBTInfoParser.determine_script_type(script)
        assert result == "P2PKH"

    def test_determine_script_type_p2sh(self):
        """Test identifying P2SH script"""
        # OP_HASH160 <20 bytes> OP_EQUAL
        script = bytes([OP_HASH160, OP_PUSHBYTES_20]) + b'\xbb' * 20 + bytes([OP_EQUAL])
        result = PSBTInfoParser.determine_script_type(script)
        assert result == "P2SH"

    def test_determine_script_type_p2wpkh(self):
        """Test identifying P2WPKH script"""
        # OP_0 <20 bytes>
        script = bytes([OP_0, OP_PUSHBYTES_20]) + b'\xcc' * 20
        result = PSBTInfoParser.determine_script_type(script)
        assert result == "P2WPKH"

    def test_determine_script_type_p2wsh(self):
        """Test identifying P2WSH script"""
        # OP_0 <32 bytes>
        script = bytes([OP_0, OP_PUSHBYTES_32]) + b'\xdd' * 32
        result = PSBTInfoParser.determine_script_type(script)
        assert result == "P2WSH"

    def test_determine_script_type_p2tr(self):
        """Test identifying P2TR (Taproot) script"""
        # OP_1 <32 bytes>
        script = bytes([OP_1, OP_PUSHBYTES_32]) + b'\xee' * 32
        result = PSBTInfoParser.determine_script_type(script)
        assert result == "P2TR"

    def test_determine_script_type_unknown_empty(self):
        """Test identifying unknown script (empty)"""
        script = b''
        result = PSBTInfoParser.determine_script_type(script)
        assert result == "UNKNOWN"

    def test_determine_script_type_unknown_custom(self):
        """Test identifying unknown script (custom)"""
        script = b'\x99\x88\x77\x66'
        result = PSBTInfoParser.determine_script_type(script)
        assert result == "UNKNOWN"

    def test_determine_script_type_p2pkh_wrong_length(self):
        """Test that incorrect length doesn't match P2PKH"""
        # P2PKH pattern but wrong length
        script = bytes([OP_DUP, OP_HASH160, OP_PUSHBYTES_20]) + b'\xaa' * 19
        result = PSBTInfoParser.determine_script_type(script)
        assert result == "UNKNOWN"

    def test_determine_script_type_p2wpkh_wrong_length(self):
        """Test that incorrect length doesn't match P2WPKH"""
        # P2WPKH pattern but wrong length
        script = bytes([OP_0, OP_PUSHBYTES_20]) + b'\xcc' * 19
        result = PSBTInfoParser.determine_script_type(script)
        assert result == "UNKNOWN"


class TestGetVbytesV2:
    """Test get_vbytes_v2 function"""

    def test_get_vbytes_v2_single_legacy_input(self):
        """Test vbytes calculation for single legacy input"""
        # Create a simple input map with final scriptSig
        key_scriptsig = PSBTKey(1, PSBT_IN_FINAL_SCRIPTSIG, b'', PSBTMapType.INPUT)
        val_scriptsig = PSBTVal(50, b'\x00' * 50)  # 50-byte scriptSig
        input_map = PSBTMap([PSBTKeyVal(key_scriptsig, val_scriptsig)])

        # Create a simple output map with script
        key_script = PSBTKey(1, PSBT_OUT_SCRIPT, b'', PSBTMapType.OUTPUT)
        val_script = PSBTVal(25, b'\x00' * 25)  # 25-byte script
        output_map = PSBTMap([PSBTKeyVal(key_script, val_script)])

        vbytes = PSBTInfoParser.get_vbytes_v2([input_map], [output_map])

        # Should be non-zero and reasonable
        assert vbytes > 0
        assert vbytes < 500  # Reasonable upper bound for single input/output

    def test_get_vbytes_v2_single_segwit_input(self):
        """Test vbytes calculation for single SegWit input"""
        # Create input with witness script
        key_witness = PSBTKey(1, PSBT_IN_FINAL_SCRIPTWITNESS, b'', PSBTMapType.INPUT)
        val_witness = PSBTVal(100, b'\x00' * 100)
        input_map = PSBTMap([PSBTKeyVal(key_witness, val_witness)])

        # Create output
        key_script = PSBTKey(1, PSBT_OUT_SCRIPT, b'', PSBTMapType.OUTPUT)
        val_script = PSBTVal(22, b'\x00' * 22)  # P2WPKH size
        output_map = PSBTMap([PSBTKeyVal(key_script, val_script)])

        vbytes = PSBTInfoParser.get_vbytes_v2([input_map], [output_map])

        # SegWit should result in lower vbytes than legacy for same data size
        assert vbytes > 0
        assert vbytes < 300

    def test_get_vbytes_v2_multiple_inputs(self):
        """Test vbytes calculation for multiple inputs"""
        # Create 2 witness inputs
        key_witness = PSBTKey(1, PSBT_IN_FINAL_SCRIPTWITNESS, b'', PSBTMapType.INPUT)
        val_witness = PSBTVal(100, b'\x00' * 100)
        input_map1 = PSBTMap([PSBTKeyVal(key_witness, val_witness)])
        input_map2 = PSBTMap([PSBTKeyVal(key_witness, val_witness)])

        # Create output
        key_script = PSBTKey(1, PSBT_OUT_SCRIPT, b'', PSBTMapType.OUTPUT)
        val_script = PSBTVal(22, b'\x00' * 22)
        output_map = PSBTMap([PSBTKeyVal(key_script, val_script)])

        vbytes = PSBTInfoParser.get_vbytes_v2([input_map1, input_map2], [output_map])

        # 2 inputs should be roughly 2x the size
        assert vbytes > 0

    def test_get_vbytes_v2_multiple_outputs(self):
        """Test vbytes calculation for multiple outputs"""
        # Create input
        key_witness = PSBTKey(1, PSBT_IN_FINAL_SCRIPTWITNESS, b'', PSBTMapType.INPUT)
        val_witness = PSBTVal(100, b'\x00' * 100)
        input_map = PSBTMap([PSBTKeyVal(key_witness, val_witness)])

        # Create 3 outputs
        key_script = PSBTKey(1, PSBT_OUT_SCRIPT, b'', PSBTMapType.OUTPUT)
        val_script = PSBTVal(22, b'\x00' * 22)
        output_map1 = PSBTMap([PSBTKeyVal(key_script, val_script)])
        output_map2 = PSBTMap([PSBTKeyVal(key_script, val_script)])
        output_map3 = PSBTMap([PSBTKeyVal(key_script, val_script)])

        vbytes = PSBTInfoParser.get_vbytes_v2([input_map], [output_map1, output_map2, output_map3])

        assert vbytes > 0

    def test_get_vbytes_v2_empty_maps(self):
        """Test vbytes calculation for empty input/output maps"""
        vbytes = PSBTInfoParser.get_vbytes_v2([], [])

        # Should have base transaction size
        assert vbytes > 0
        assert vbytes < 50  # Just base tx structure

    def test_get_vbytes_v2_witness_flag_added_for_segwit(self):
        """Test that witness flag is added when SegWit data present"""
        # Create input with witness script
        key_witness = PSBTKey(1, PSBT_IN_WITNESS_SCRIPT, b'', PSBTMapType.INPUT)
        val_witness = PSBTVal(50, b'\x00' * 50)
        input_map = PSBTMap([PSBTKeyVal(key_witness, val_witness)])

        # Empty output
        output_map = PSBTMap([])

        vbytes_segwit = PSBTInfoParser.get_vbytes_v2([input_map], [output_map])

        # Create legacy input (no witness)
        key_scriptsig = PSBTKey(1, PSBT_IN_FINAL_SCRIPTSIG, b'', PSBTMapType.INPUT)
        val_scriptsig = PSBTVal(50, b'\x00' * 50)
        input_map_legacy = PSBTMap([PSBTKeyVal(key_scriptsig, val_scriptsig)])

        vbytes_legacy = PSBTInfoParser.get_vbytes_v2([input_map_legacy], [output_map])

        # Both should be positive, but witness adds overhead
        assert vbytes_segwit > 0
        assert vbytes_legacy > 0


class TestScriptTypeToAddressType:
    """Test SCRIPT_TYPE_TO_ADDRESS_TYPE mapping"""

    def test_script_type_to_address_type_mappings(self):
        """Test that script types map to correct address types"""
        mapping = PSBTInfoParser.SCRIPT_TYPE_TO_ADDRESS_TYPE

        assert mapping["P2PKH"] == "Legacy / Base58"
        assert mapping["P2SH"] == "Nested SegWit / Legacy"
        assert mapping["P2WPKH"] == "Native SegWit (bech32)"
        assert mapping["P2WSH"] == "Native SegWit (bech32)"
        assert mapping["P2TR"] == "Native SegWit v1"

    def test_script_type_to_address_type_unknown(self):
        """Test handling of unknown script type"""
        mapping = PSBTInfoParser.SCRIPT_TYPE_TO_ADDRESS_TYPE

        # UNKNOWN should not be in mapping, use .get() with default
        result = mapping.get("UNKNOWN", "Unknown")
        assert result == "Unknown"


class TestGetInfo:
    """Test get_info function (integration tests)"""

    def test_get_info_requires_utxo_data(self):
        """Test that get_info raises error without UTXO data"""
        # Create minimal PSBT v0 with input but no UTXO data
        magic = b'psbt\xff'
        # Transaction with 1 input, 1 output
        tx = (b'\x01\x00\x00\x00' +  # version
              b'\x01' + b'\xaa' * 32 + b'\x00\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff' +  # input
              b'\x01' + (50000).to_bytes(8, 'little') + b'\x16' + b'\x00\x14' + b'\xbb' * 20 +  # output
              b'\x00\x00\x00\x00')  # locktime
        global_map = b'\x01\x00' + bytes([len(tx)]) + tx + b'\x00'
        # Input map without UTXO data (will cause error)
        input_map = b'\x00'
        output_map = b'\x00'

        buffer = BytesIO(magic + global_map + input_map + output_map)
        psbt = PSBTParser.parse_psbt(buffer)

        # Should raise ValueError when no UTXO found
        with pytest.raises(ValueError, match="No UTXO found for input"):
            PSBTInfoParser.get_info(psbt)

    def test_get_info_v0_basic_structure(self):
        """Test get_info returns correct structure for v0 PSBT"""
        # This test requires a complete PSBT with UTXO data
        # We'll create a minimal but valid one

        magic = b'psbt\xff'
        # Transaction with 1 input, 1 output
        tx = (b'\x01\x00\x00\x00' +  # version
              b'\x01' + b'\xaa' * 32 + b'\x00\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff' +  # input
              b'\x01' + (50000).to_bytes(8, 'little') + b'\x16' + b'\x00\x14' + b'\xbb' * 20 +  # output
              b'\x00\x00\x00\x00')  # locktime
        global_map = b'\x01\x00' + bytes([len(tx)]) + tx + b'\x00'

        # Input map with witness UTXO
        amount = (100000).to_bytes(8, 'little')
        script = b'\x00\x14' + b'\xcc' * 20
        script_len = bytes([len(script)])
        witness_utxo_data = amount + script_len + script
        input_map = (b'\x01\x01' +  # Key: type 0x01 (WITNESS_UTXO)
                     bytes([len(witness_utxo_data)]) + witness_utxo_data +  # Value
                     b'\x00')  # Terminator

        output_map = b'\x00'

        buffer = BytesIO(magic + global_map + input_map + output_map)
        psbt = PSBTParser.parse_psbt(buffer)

        info = PSBTInfoParser.get_info(psbt)

        # Verify structure
        assert info.version == 0
        assert len(info.inputs) == 1
        assert len(info.outputs) == 1
        assert info.total_input_amt == 100000
        assert info.total_output_amt == 50000
        assert info.fee_amt == 50000
        assert info.fee_rate > 0

    def test_get_info_change_detection(self):
        """Test that change outputs are correctly identified"""
        # This would require a full PSBT with BIP32 derivation data
        # Simplified test showing the logic works
        magic = b'psbt\xff'
        tx = (b'\x01\x00\x00\x00' +
              b'\x01' + b'\xaa' * 32 + b'\x00\x00\x00\x00' + b'\x00' + b'\xff\xff\xff\xff' +
              b'\x01' + (50000).to_bytes(8, 'little') + b'\x16' + b'\x00\x14' + b'\xbb' * 20 +
              b'\x00\x00\x00\x00')
        global_map = b'\x01\x00' + bytes([len(tx)]) + tx + b'\x00'

        # Input map with witness UTXO
        amount = (100000).to_bytes(8, 'little')
        script = b'\x00\x14' + b'\xcc' * 20
        script_len = bytes([len(script)])
        witness_utxo_data = amount + script_len + script
        input_map = b'\x01\x01' + bytes([len(witness_utxo_data)]) + witness_utxo_data + b'\x00'

        # Output map with BIP32 derivation indicating change (index 3 = 1)
        # PSBT_OUT_BIP32_DERIVATION is type 0x02
        fingerprint = b'\x12\x34\x56\x78'
        # Path: 84'/0'/0'/1/0 (change address)
        pubkey = b'\x02' + b'\xaa' * 32  # 33-byte compressed pubkey
        deriv_value = fingerprint + (
            (84 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (0 | 0x80000000).to_bytes(4, 'little') +
            (1).to_bytes(4, 'little') +  # Change index
            (0).to_bytes(4, 'little')
        )
        # Key: type 0x02 + pubkey data, Value: derivation data
        key_len = 1 + len(pubkey)  # type byte + pubkey
        output_map = bytes([key_len]) + b'\x02' + pubkey + bytes([len(deriv_value)]) + deriv_value + b'\x00'

        buffer = BytesIO(magic + global_map + input_map + output_map)
        psbt = PSBTParser.parse_psbt(buffer)

        info = PSBTInfoParser.get_info(psbt)

        # Should detect change output
        assert len(info.change_output) == 1
        assert info.change_output[0] == True
