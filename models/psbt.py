"""
PSBT data structure classes
"""
import json
from enum import Enum

class PSBTMapType(Enum):
    """Enum for PSBT map types."""
    GLOBAL = "GLOBAL"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

# Global Key Types Dictionary (BIP-174)
PSBT_GLOBAL_TYPES = {
    0: "PSBT_GLOBAL_UNSIGNED_TX",
    1: "PSBT_GLOBAL_XPUB",
    2: "PSBT_GLOBAL_TX_VERSION",
    3: "PSBT_GLOBAL_FALLBACK_LOCKTIME",
    4: "PSBT_GLOBAL_INPUT_COUNT",
    5: "PSBT_GLOBAL_OUTPUT_COUNT",
    6: "PSBT_GLOBAL_TX_MODIFIABLE",
    7: "PSBT_GLOBAL_SP_ECDH_SHARE",
    8: "PSBT_GLOBAL_SP_DLEQ_PROOF",
    251: "PSBT_GLOBAL_VERSION",
    252: "PSBT_GLOBAL_PROPRIETARY"
}

# Per-Input Key Types Dictionary (BIP-174)
PSBT_IN_TYPES = {
    0: "PSBT_IN_NON_WITNESS_UTXO",
    1: "PSBT_IN_WITNESS_UTXO",
    2: "PSBT_IN_PARTIAL_SIG",
    3: "PSBT_IN_SIGHASH_TYPE",
    4: "PSBT_IN_REDEEM_SCRIPT",
    5: "PSBT_IN_WITNESS_SCRIPT",
    6: "PSBT_IN_BIP32_DERIVATION",
    7: "PSBT_IN_FINAL_SCRIPTSIG",
    8: "PSBT_IN_FINAL_SCRIPTWITNESS",
    9: "PSBT_IN_POR_COMMITMENT",
    10: "PSBT_IN_RIPEMD160",
    11: "PSBT_IN_SHA256",
    12: "PSBT_IN_HASH160",
    13: "PSBT_IN_HASH256",
    14: "PSBT_IN_PREVIOUS_TXID",
    15: "PSBT_IN_OUTPUT_INDEX",
    16: "PSBT_IN_SEQUENCE",
    17: "PSBT_IN_REQUIRED_TIME_LOCKTIME",
    18: "PSBT_IN_REQUIRED_HEIGHT_LOCKTIME",
    19: "PSBT_IN_TAP_KEY_SIG",
    20: "PSBT_IN_TAP_SCRIPT_SIG",
    21: "PSBT_IN_TAP_LEAF_SCRIPT",
    22: "PSBT_IN_TAP_BIP32_DERIVATION",
    23: "PSBT_IN_TAP_INTERNAL_KEY",
    24: "PSBT_IN_TAP_MERKLE_ROOT",
    26: "PSBT_IN_MUSIG2_PUB_NONCE",
    27: "PSBT_IN_MUSIG2_PARTICIPANT_PUBKEYS",
    28: "PSBT_IN_MUSIG2_PARTIAL_SIG",
    29: "PSBT_IN_SP_ECDH_SHARE",
    30: "PSBT_IN_SP_DLEQ_PROOF",
    252: "PSBT_IN_PROPRIETARY"
}

# Per-Output Key Types Dictionary (BIP-174)
PSBT_OUT_TYPES = {
    0: "PSBT_OUT_REDEEM_SCRIPT",
    1: "PSBT_OUT_WITNESS_SCRIPT",
    2: "PSBT_OUT_BIP32_DERIVATION",
    3: "PSBT_OUT_AMOUNT",
    4: "PSBT_OUT_SCRIPT",
    5: "PSBT_OUT_TAP_INTERNAL_KEY",
    6: "PSBT_OUT_TAP_TREE",
    7: "PSBT_OUT_TAP_BIP32_DERIVATION",
    252: "PSBT_OUT_PROPRIETARY"
}

# Automatically create constants from dictionaries
globals().update({name: value for value, name in PSBT_GLOBAL_TYPES.items()})
globals().update({name: value for value, name in PSBT_IN_TYPES.items()})
globals().update({name: value for value, name in PSBT_OUT_TYPES.items()})

# Export all constants and classes for wildcard import
__all__ = [
    'PSBTKey', 'PSBTVal', 'PSBTKeyVal', 'PSBTMap', 'PSBT', 'PSBTMapType',
    'PSBT_GLOBAL_TYPES', 'PSBT_IN_TYPES', 'PSBT_OUT_TYPES',
] + list(PSBT_GLOBAL_TYPES.values()) + list(PSBT_IN_TYPES.values()) + list(PSBT_OUT_TYPES.values())

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
