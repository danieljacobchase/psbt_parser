"""
PSBT data structure classes
"""
import json
from enum import Enum
from models.constants import PSBT_GLOBAL_TYPES, PSBT_IN_TYPES, PSBT_OUT_TYPES

class PSBTMapType(Enum):
    """Enum for PSBT map types."""
    GLOBAL = "GLOBAL"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

class PSBTKey:
    def __init__(self, key_len: int, key_type: int, key_data: bytes, map_type: PSBTMapType):
        self.key_len = key_len
        self.key_type = key_type
        self.key_data = key_data
        self.type = map_type

    def to_string(self):
        # Select the appropriate dictionary based on the type field
        if self.type == PSBTMapType.GLOBAL:
            key_type_name = PSBT_GLOBAL_TYPES.get(self.key_type, "UNKNOWN")
        elif self.type == PSBTMapType.INPUT:
            key_type_name = PSBT_IN_TYPES.get(self.key_type, "UNKNOWN")
        elif self.type == PSBTMapType.OUTPUT:
            key_type_name = PSBT_OUT_TYPES.get(self.key_type, "UNKNOWN")
        else:
            key_type_name = "UNKNOWN"

        return json.dumps({
            "key_len": self.key_len,
            "key_type": self.key_type,
            "key_type_name": key_type_name,
            "key_data": self.key_data.hex(),
            "type": self.type.value
        }, indent=2)

class PSBTVal:
    def __init__(self, val_len: int, val_data: bytes):
        self.val_len = val_len
        self.val_data = val_data

    def to_string(self):
        return json.dumps({
            "val_len": self.val_len,
            "val_data": self.val_data.hex()
        }, indent=2)

class PSBTKeyVal:
    def __init__(self, key: PSBTKey, val: PSBTVal):
        self.key = key
        self.val = val

    def to_string(self):
        return json.dumps({
            "key": json.loads(self.key.to_string()),
            "val": json.loads(self.val.to_string())
        }, indent=2)

class PSBTMap:
    def __init__(self, map: list[PSBTKeyVal]):
        self.map = map

    def to_string(self):
        map_list = [json.loads(kv.to_string()) for kv in self.map]
        return json.dumps(map_list, indent=2)

class PSBT:
    def __init__(self, version: int, global_map: PSBTMap, input_maps: list[PSBTMap], output_maps: list[PSBTMap]):
        self.version = version
        self.global_map = global_map
        self.input_maps = input_maps
        self.output_maps = output_maps

    def to_string(self):
        return json.dumps({
            "version": self.version,
            "global_map": json.loads(self.global_map.to_string()),
            "input_maps": [json.loads(input_map.to_string()) for input_map in self.input_maps],
            "output_maps": [json.loads(output_map.to_string()) for output_map in self.output_maps]
        }, indent=2)


class PSBTInOutInfo:
    """Information about a PSBT input or output."""

    def __init__(self, amount: int, address_type: str, script_type: str):
        """
        Initialize a PSBTInOutInfo object.

        Args:
            amount: Amount in satoshis
            address_type: Type of address (e.g., "P2PKH", "P2WPKH", "P2SH")
            script_type: Type of script (e.g., "legacy", "segwit", "taproot")
        """
        self.amount = amount
        self.address_type = address_type
        self.script_type = script_type

    def to_string(self):
        """Convert to JSON string representation."""
        return json.dumps({
            "amount": self.amount,
            "address_type": self.address_type,
            "script_type": self.script_type
        }, indent=2)


class PSBTInfo:
    """Information extracted from a PSBT."""

    def __init__(self, version: int, total_input_amt: int, total_output_amt: int, fee_amt: int, fee_rate: float, change_output: list[bool], inputs: list, outputs: list):
        """
        Initialize a PSBTInfo object.

        Args:
            version: PSBT version (0 or 2)
            total_input_amt: Total input amount in satoshis
            total_output_amt: Total output amount in satoshis
            fee_amt: Transaction fee in satoshis
            fee_rate: Fee rate in sats/vbyte
            change_output: Bool array indicating which outputs are change
            inputs: List of input information
            outputs: List of output information
        """
        self.version = version
        self.total_input_amt = total_input_amt
        self.total_output_amt = total_output_amt
        self.fee_amt = fee_amt
        self.fee_rate = fee_rate
        self.change_output = change_output
        self.inputs = inputs
        self.outputs = outputs

    def to_string(self):
        """Convert to JSON string representation."""
        # Convert bool array to string representation
        change_output_str = [str(is_change) for is_change in self.change_output]

        return json.dumps({
            "version": self.version,
            "total_input_amt": self.total_input_amt,
            "total_output_amt": self.total_output_amt,
            "fee_amt": self.fee_amt,
            "fee_rate": self.fee_rate,
            "change_output": change_output_str,
            "inputs": [json.loads(inp.to_string()) for inp in self.inputs],
            "outputs": [json.loads(out.to_string()) for out in self.outputs]
        }, indent=2)
