#!/usr/bin/env python3
"""
PSBT Parser - Parse and display Bitcoin Partially Signed Bitcoin Transactions
"""
import sys
from io import BytesIO
from parser.psbt_parser import parse_psbt

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <filename>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        hex_string = f.read().strip()

    byte_data = bytes.fromhex(hex_string)
    buffer = BytesIO(byte_data)
    psbt = parse_psbt(buffer)

    print(psbt.to_string())

