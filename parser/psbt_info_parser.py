"""
PSBT Info Parser - Extract information from PSBT data.
"""

from models.constants import *
from models.constants import PSBT_IN_NON_WITNESS_UTXO, PSBT_IN_WITNESS_UTXO, PSBT_IN_OUTPUT_INDEX, PSBT_OUT_AMOUNT, PSBT_OUT_SCRIPT, PSBT_OUT_BIP32_DERIVATION, PSBT_GLOBAL_UNSIGNED_TX
from models.psbt import PSBTInOutInfo, PSBTInfo
from parser.psbt_key_parser import PSBTKeyParser
from parser.transaction_parser import TransactionParser

class PSBTInfoParser:
    """Parser for extracting information from PSBTs."""

    # Script type to address type mapping
    SCRIPT_TYPE_TO_ADDRESS_TYPE = {
        "P2PKH": "Legacy / Base58",
        "P2SH": "Nested SegWit / Legacy",
        "P2WPKH": "Native SegWit (bech32)",
        "P2WSH": "Native SegWit (bech32)",
        "P2TR": "Native SegWit v1"
    }

    @staticmethod
    def find_key_index(input_map, key_type):
        """
        Find the index of a specific key type in an input map.

        Args:
            input_map: PSBTMap object to search
            key_type: Key type value to search for

        Returns:
            int: Index of the key if found, -1 otherwise
        """
        for i, key_val in enumerate(input_map.map):
            if key_val.key.key_type == key_type:
                return i
        return -1

    @staticmethod
    def get_vbytes_v2(input_map_list: list, output_map_list: list) -> float:
        """
        Calculate the virtual size (vbytes) for a PSBT v2 transaction.

        Args:
            input_list: List of input information

        Returns:
            float: Virtual size in vbytes
        """
        witness_size = 0
        is_segwit = False

        # Base size is the size of the transaction without witness data
        base_size = 4 # version
        base_size += 1 # input count (estimate)
        base_size += 1 # output count (estimate)
        base_size += 4 # locktime

        # Calculate base (and, optionally, witness size) for inputs
        for input_map in input_map_list:
            base_size += 32 # txid
            base_size += 4 # vout
            base_size += 1 # script size (estimate)
            base_size += 4 # sequence number

            # Iterate through key-value pairs in this input map
            for key_val in input_map.map:
                if key_val.key.key_type == PSBT_IN_WITNESS_SCRIPT:
                    witness_size += len(key_val.val.val_data)
                    is_segwit = True
                elif key_val.key.key_type == PSBT_IN_FINAL_SCRIPTSIG:
                    base_size += len(key_val.val.val_data)
                elif key_val.key.key_type == PSBT_IN_FINAL_SCRIPTWITNESS:
                    witness_size += len(key_val.val.val_data)
                    is_segwit = True

        # If SegWit, add witness size to base size
        if is_segwit:
            base_size += 2 # witness flag

        # Calculate base size for outputs
        for output_map in output_map_list:
            base_size += 8 # amount
            base_size += 1 # script size (estimate)

            # Iterate through key-value pairs in this output map
            for key_val in output_map.map:
                if key_val.key.key_type == PSBT_OUT_SCRIPT:
                    base_size += len(key_val.val.val_data)

        # Calculate weight and vbytes
        weight = (base_size * 4) + witness_size
        vbytes = weight / 4

        return vbytes

    @staticmethod
    def determine_script_type(script: bytes):
        """
        Determine the script type from a scriptPubKey.

        Args:
            script: Script bytes (scriptPubKey)

        Returns:
            str: Script type (e.g., "P2PKH", "P2WPKH", "P2SH", "P2WSH", "P2TR")
        """
        script_len = len(script)

        # P2PKH: OP_DUP OP_HASH160 <20 bytes> OP_EQUALVERIFY OP_CHECKSIG (25 bytes)
        if script_len == 25 \
            and script[0] == OP_DUP and script[1] == OP_HASH160 and script[2] == OP_PUSHBYTES_20 \
            and script[23] == OP_EQUALVERIFY and script[24] == OP_CHECKSIG:
                return "P2PKH"

        # P2SH: OP_HASH160 <20 bytes> OP_EQUAL (23 bytes)
        if script_len == 23 \
            and script[0] == OP_HASH160 and script[1] == OP_PUSHBYTES_20 \
            and script[22] == OP_EQUAL:
                return "P2SH"

        # P2WPKH: OP_0 <20 bytes> (22 bytes)
        if script_len == 22 \
            and script[0] == OP_0 \
            and script[1] == OP_PUSHBYTES_20:
                return "P2WPKH"

        # P2WSH: OP_0 <32 bytes> (34 bytes)
        if script_len == 34 \
            and script[0] == OP_0 \
            and script[1] == OP_PUSHBYTES_32:
                return "P2WSH"

        # P2TR: OP_1 <32 bytes> (34 bytes)
        if script_len == 34 \
            and script[0] == OP_1 and script[1] == OP_PUSHBYTES_32:
                return "P2TR"

        return "UNKNOWN"

    @staticmethod
    def get_info(psbt):
        """
        Extract information from a PSBT.

        Args:
            psbt: PSBT object to extract information from

        Returns:
            dict: Information about the PSBT
        """

        # get global map data as transaction
        if psbt.version == 0:
            from io import BytesIO
            key_index = PSBTInfoParser.find_key_index(psbt.global_map, PSBT_GLOBAL_UNSIGNED_TX)
            tx_data = psbt.global_map.map[key_index].val.val_data
            this_tx = TransactionParser.parse_transaction(BytesIO(tx_data))

        # Get Inputs (Same for v0 and v2)
        input_list = []
        for i in range(len(psbt.input_maps)):
            input_map = psbt.input_maps[i]

            non_witness_utxo_index = PSBTInfoParser.find_key_index(input_map, PSBT_IN_NON_WITNESS_UTXO)
            witness_utxo_index = PSBTInfoParser.find_key_index(input_map, PSBT_IN_WITNESS_UTXO)

            # get output index from input transaction (method differs for v0 and v2)
            if psbt.version == 0:
                output_index = int.from_bytes(this_tx.inputs[i].vout, 'little')
            else:
                output_index_key = PSBTInfoParser.find_key_index(input_map, PSBT_IN_OUTPUT_INDEX)
                output_index = PSBTKeyParser.parse_key_PSBT_IN_OUTPUT_INDEX(input_map.map[output_index_key].val.val_data)

            if non_witness_utxo_index != -1:
                # parse non-witness UTXO
                input_tx = PSBTKeyParser.parse_key_PSBT_IN_NON_WITNESS_UTXO(input_map.map[non_witness_utxo_index].val.val_data)
                # get amount from input transaction
                amount = input_tx.outputs[output_index].amount
                # get script for determining type
                script = input_tx.outputs[output_index].spk
            elif witness_utxo_index != -1:
                # parse witness UTXO
                witness_utxo = PSBTKeyParser.parse_key_PSBT_IN_WITNESS_UTXO(input_map.map[witness_utxo_index].val.val_data)
                # get amount from witness UTXO
                amount = witness_utxo.amount
                # get script from witness UTXO (need to convert from hex)
                script = bytes.fromhex(witness_utxo.script_hash)
            else:
                raise ValueError("No UTXO found for input " + str(i))

            # determine script type
            script_type = PSBTInfoParser.determine_script_type(script)
            # determine address type
            address_type = PSBTInfoParser.SCRIPT_TYPE_TO_ADDRESS_TYPE.get(script_type, "Unknown")

            # add to input list
            input_list.append(PSBTInOutInfo(amount, address_type, script_type))

        # Get Outputs (Different for v0 and v2)
        output_list = []
        if psbt.version == 0:
            for i in range(len(this_tx.outputs)):
                # get amount from output transaction
                amount = this_tx.outputs[i].amount
                # determine script type
                script_type = PSBTInfoParser.determine_script_type(this_tx.outputs[i].spk)
                # determine address type
                address_type = PSBTInfoParser.SCRIPT_TYPE_TO_ADDRESS_TYPE.get(script_type, "Unknown")
                # add to output list
                output_list.append(PSBTInOutInfo(amount, address_type, script_type))
        else:
            for i in range(len(psbt.output_maps)):
                output_map = psbt.output_maps[i]
                # get amount from output map
                amount_key = PSBTInfoParser.find_key_index(output_map, PSBT_OUT_AMOUNT)
                amount = PSBTKeyParser.parse_key_PSBT_OUT_AMOUNT(output_map.map[amount_key].val.val_data)
                # determine script type
                script_key = PSBTInfoParser.find_key_index(output_map, PSBT_OUT_SCRIPT)
                script_type = PSBTInfoParser.determine_script_type(PSBTKeyParser.parse_key_PSBT_OUT_SCRIPT(output_map.map[script_key].val.val_data))
                # determine address type
                address_type = PSBTInfoParser.SCRIPT_TYPE_TO_ADDRESS_TYPE.get(script_type, "Unknown")
                # add to output list
                output_list.append(PSBTInOutInfo(amount, address_type, script_type))

        # Calculate fee
        input_total = sum(input.amount for input in input_list)
        output_total = sum(output.amount for output in output_list)
        fee = input_total - output_total

        # Calculate fee rate
        if psbt.version == 0:
            vbytes = this_tx.vbytes
        else:
            vbytes = PSBTInfoParser.get_vbytes_v2(psbt.input_maps, psbt.output_maps)
        fee_rate = fee / vbytes

        # Create change output bool array
        change_output = [False] * len(output_list)
        for i in range(len(psbt.output_maps)):
            output_map = psbt.output_maps[i]
            # Look for BIP32 derivation path in this output
            deriv_index = PSBTInfoParser.find_key_index(output_map, PSBT_OUT_BIP32_DERIVATION)
            if deriv_index != -1:
                derivation = PSBTKeyParser.parse_key_PSBT_OUT_BIP32_DERIVATION(output_map.map[deriv_index].val.val_data)
                change_output[i] = derivation.is_change

        return PSBTInfo(psbt.version, input_total, output_total, fee, fee_rate, vbytes, change_output, input_list, output_list)