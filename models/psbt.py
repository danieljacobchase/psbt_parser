"""
PSBT data structure classes
"""
import json
from enum import Enum
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from models.constants import PSBT_GLOBAL_TYPES, PSBT_IN_TYPES, PSBT_OUT_TYPES

class PSBTMapType(Enum):
    """Enum for PSBT map types."""
    GLOBAL = "GLOBAL"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

class PSBTKey(BaseModel):
    model_config = ConfigDict(populate_by_name=True, use_enum_values=False)

    key_len: int = Field(ge=0)
    key_type: int = Field(ge=0)
    key_data: bytes
    map_type: PSBTMapType = Field(alias='type')

    @model_validator(mode='after')
    def check_size_matches(self):
        # key_len should equal len(key_data) + compact_size_length(key_type)
        # For PSBT key types (all < 253), compact size is always 1 byte
        if self.key_type < 0xfd:
            key_type_len = 1
        elif self.key_type <= 0xffff:
            key_type_len = 3
        elif self.key_type <= 0xffffffff:
            key_type_len = 5
        else:
            key_type_len = 9

        expected_len = len(self.key_data) + key_type_len
        if self.key_len != expected_len:
            raise ValueError(f'key_len {self.key_len} != len(key_data) + key_type_len ({expected_len})')
        return self

    def to_string(self):
        # Select the appropriate dictionary based on the type field
        if self.map_type == PSBTMapType.GLOBAL:
            key_type_name = PSBT_GLOBAL_TYPES.get(self.key_type, "UNKNOWN")
        elif self.map_type == PSBTMapType.INPUT:
            key_type_name = PSBT_IN_TYPES.get(self.key_type, "UNKNOWN")
        elif self.map_type == PSBTMapType.OUTPUT:
            key_type_name = PSBT_OUT_TYPES.get(self.key_type, "UNKNOWN")
        else:
            key_type_name = "UNKNOWN"

        return json.dumps({
            "key_len": self.key_len,
            "key_type": self.key_type,
            "key_type_name": key_type_name,
            "key_data": self.key_data.hex(),
            "type": self.map_type.value
        }, indent=2)

class PSBTVal(BaseModel):
    val_len: int = Field(ge=0)
    val_data: bytes

    @model_validator(mode='after')
    def check_size_matches(self):
        if len(self.val_data) != self.val_len:
            raise ValueError(f'val_data length {len(self.val_data)} != val_len {self.val_len}')
        return self

    def to_string(self):
        return json.dumps({
            "val_len": self.val_len,
            "val_data": self.val_data.hex()
        }, indent=2)

class PSBTKeyVal(BaseModel):
    key: PSBTKey
    val: PSBTVal

    def to_string(self):
        return json.dumps({
            "key": json.loads(self.key.to_string()),
            "val": json.loads(self.val.to_string())
        }, indent=2)

class PSBTMap(BaseModel):
    map: list[PSBTKeyVal]

    def to_string(self):
        map_list = [json.loads(kv.to_string()) for kv in self.map]
        return json.dumps(map_list, indent=2)

class PSBT(BaseModel):
    version: int = Field(ge=0)  # PSBT version must be 0 or 2 (no v1 exists)
    global_map: PSBTMap
    input_maps: list[PSBTMap]
    output_maps: list[PSBTMap]

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: int) -> int:
        if v not in (0, 2):
            raise ValueError(f'PSBT version must be 0 or 2 (v1 does not exist), got {v}')
        return v

    def to_string(self):
        return json.dumps({
            "version": self.version,
            "global_map": json.loads(self.global_map.to_string()),
            "input_maps": [json.loads(input_map.to_string()) for input_map in self.input_maps],
            "output_maps": [json.loads(output_map.to_string()) for output_map in self.output_maps]
        }, indent=2)


class PSBTInOutInfo(BaseModel):
    """Information about a PSBT input or output."""

    amount: int = Field(ge=0)  # Amount in satoshis, must be non-negative
    address_type: str          # Type of address (e.g., "P2PKH", "P2WPKH", "P2SH")
    script_type: str           # Type of script (e.g., "legacy", "segwit", "taproot")

    def to_string(self):
        """Convert to JSON string representation."""
        return json.dumps({
            "amount": self.amount,
            "address_type": self.address_type,
            "script_type": self.script_type
        }, indent=2)


class PSBTInfo(BaseModel):
    """Information extracted from a PSBT."""

    version: int = Field(ge=0)  # PSBT version must be 0 or 2 (no v1 exists)
    total_input_amt: int = Field(ge=0)
    total_output_amt: int = Field(ge=0)
    fee_amt: int = Field(ge=0)
    fee_rate: float = Field(ge=0)
    vbytes: float = Field(gt=0)
    change_output: list[bool]
    inputs: list[PSBTInOutInfo]
    outputs: list[PSBTInOutInfo]

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: int) -> int:
        if v not in (0, 2):
            raise ValueError(f'PSBT version must be 0 or 2 (v1 does not exist), got {v}')
        return v

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
            "vbytes": self.vbytes,
            "change_output": change_output_str,
            "inputs": [json.loads(inp.to_string()) for inp in self.inputs],
            "outputs": [json.loads(out.to_string()) for out in self.outputs]
        }, indent=2)
