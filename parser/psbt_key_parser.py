"""
PSBT Key Parser - Parse and extract data from PSBT keys.
"""

from io import BytesIO
from models.keys import PsbtKeyInWitnessUTXO, PsbtKeyOutBIP32Derivation
from parser.transaction_parser import TransactionParser

# Bitcoin Script OP codes
OP_0 = bytes([0])
OP_PUSHBYTES_20 = bytes([20])


class PSBTKeyParser:
    """Parser for PSBT key data with static parsing methods."""

    @staticmethod
    def parse_key_PSBT_IN_WITNESS_UTXO(data: bytes):
        """
        Parse PSBT_IN_WITNESS_UTXO key data.

        Args:
            data: Raw key data bytes

        Returns:
            PsbtKeyInWitnessUTXO: Parsed witness UTXO information
        """
        from parser.utils import parse_compact_size
        buffer = BytesIO(data)

        # retrieve UTXO amount in sats (8 bytes)
        amount = buffer.read(8)

        # read script length as compact size
        script_len, _ = parse_compact_size(buffer)

        # retrieve scriptPubKey
        script = buffer.read(script_len)

        return PsbtKeyInWitnessUTXO(
            amount = int.from_bytes(amount, "little"),
            script_hash = script.hex()
        )

    @staticmethod
    def parse_key_PSBT_OUT_BIP32_DERIVATION(data: bytes):
        """
        Parse PSBT_OUT_BIP32_DERIVATION key data.

        Args:
            data: Raw key data bytes

        Returns:
            PsbtKeyOutBIP32Derivation: Parsed BIP32 derivation information
        """
        buffer = BytesIO(data)

        # Read 4-byte fingerprint
        fingerprint = buffer.read(4)

        # Parse 5 derivation path indices
        indices = []
        hardened = []

        for _ in range(5):
            # Read 4 bytes for each index
            index_bytes = buffer.read(4)
            index_value = int.from_bytes(index_bytes, "little")

            # Check if hardened using bitwise AND with 0x80000000
            is_hardened = (index_value & 0x80000000) != 0

            # Get the actual index value (mask off the hardened bit)
            actual_index = index_value & 0x7FFFFFFF

            indices.append(actual_index)
            hardened.append(is_hardened)

        return PsbtKeyOutBIP32Derivation(
            fingerprint = fingerprint.hex(),
            indices = indices,
            hardened = hardened,
            is_change = True if len(indices) >= 4 and indices[3] == 1 else False
        )

    @staticmethod
    def parse_key_PSBT_IN_NON_WITNESS_UTXO(data: bytes):
        """
        Parse PSBT_IN_NON_WITNESS_UTXO key data.

        Args:
            data: Raw transaction data bytes

        Returns:
            Transaction: Parsed transaction object
        """
        buffer = BytesIO(data)
        return TransactionParser.parse_transaction(buffer)

    @staticmethod
    def parse_key_PSBT_IN_PREVIOUS_TXID(data: bytes):
        """
        Parse PSBT_IN_PREVIOUS_TXID key data.

        Args:
            data: Raw txid bytes

        Returns:
            bytes: Transaction ID as bytes
        """
        return data

    @staticmethod
    def parse_key_PSBT_IN_OUTPUT_INDEX(data: bytes):
        """
        Parse PSBT_IN_OUTPUT_INDEX key data.

        Args:
            data: Raw output index bytes

        Returns:
            int: Output index
        """
        return int.from_bytes(data, "little")

    @staticmethod
    def parse_key_PSBT_OUT_AMOUNT(data: bytes):
        """
        Parse PSBT_OUT_AMOUNT key data.

        Args:
            data: Raw amount bytes

        Returns:
            int: Amount in satoshis
        """
        return int.from_bytes(data, "little")

    @staticmethod
    def parse_key_PSBT_OUT_SCRIPT(data: bytes):
        """
        Parse PSBT_OUT_SCRIPT key data.

        Args:
            data: Raw script bytes

        Returns:
            bytes: Script as byte array
        """
        return data