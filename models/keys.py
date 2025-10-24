"""
PSBT Key data models
"""

import json

class PsbtKeyInWitnessUTXO:
    """Model for PSBT_IN_WITNESS_UTXO data."""

    def __init__(self, amount: int, script_hash: str):
        """
        Initialize a PsbtKeyInWitnessUTXO object.

        Args:
            amount: Amount in satoshis
            script_hash: Script hash as hex string
        """
        self.amount = amount
        self.script_hash = script_hash

    def to_string(self):
        """Convert to JSON string representation."""
        return json.dumps({
            "amount": self.amount,
            "script_hash": self.script_hash
        })

class PsbtKeyOutBIP32Derivation:
    """Model for PSBT_OUT_BIP32_DERIVATION data."""

    def __init__(self, fingerprint: bytes, indices: list[int], hardened: list[bool], is_change: bool):
        """
        Initialize a PsbtKeyOutBIP32Derivation object.

        Args:
            fingerprint: Master key fingerprint as bytes
            indices: List of derivation path indices
            hardened: List of booleans indicating if each index is hardened
            is_change: Boolean indicating if the output is a change output
        """
        self.fingerprint = fingerprint
        self.indices = indices
        self.hardened = hardened
        self.is_change = is_change

    def to_string(self):
        """Convert to JSON string representation."""
        # Build path string in format: m/44'/0'/0'/0/0
        path_parts = ["m"]
        for i, index in enumerate(self.indices):
            part = str(index)
            if self.hardened[i]:
                part += "'"
            path_parts.append(part)
        path = "/".join(path_parts)

        return json.dumps({
            "fingerprint": self.fingerprint.hex(),
            "path": path,
            "is_change": self.is_change
        })
