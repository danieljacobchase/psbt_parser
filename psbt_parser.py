#!/usr/bin/env python3
"""
PSBT Parser - Parse and display Bitcoin Partially Signed Bitcoin Transactions
"""
import sys
import json
from io import BytesIO
from parser.psbt_parser import PSBTParser
from parser.psbt_info_parser import PSBTInfoParser
from api.mempool import MempoolAPI
from psbt_report import PSBTReport

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python psbt_parser.py <filename>", file=sys.stderr)
        sys.exit(1)

    # Read PSBT from file and load into buffer
    filename = sys.argv[1]
    if filename.endswith('.psbt'):
        # Binary PSBT file
        with open(filename, 'rb') as f:
            byte_data = f.read()
    else:
        # Hex-encoded PSBT file (.txt or other)
        with open(filename, 'r') as f:
            hex_string = f.read().strip()
        byte_data = bytes.fromhex(hex_string)
    buffer = BytesIO(byte_data)

    # Parse PSBT
    psbt = PSBTParser.parse_psbt(buffer)

    # Parse PSBT info
    try:
        psbt_info = PSBTInfoParser.get_info(psbt)
    except ValueError as e:
        if "No UTXO found" in str(e):
            # Early-stage PSBT without UTXO data
            print("\nNote: This PSBT is at an early stage (creator/constructor) and lacks")
            print("      UTXO data needed for amount and fee analysis.")
            print(f"\nPSBT Version: {psbt.version}")
            print(f"Inputs: {len(psbt.input_maps)}")
            print(f"Outputs: {len(psbt.output_maps)}")
            sys.exit(0)
        else:
            raise

    # Get recommended fee rates from mempool
    mempool = MempoolAPI()
    recommended_fee_rates = mempool.get_recommendeed_fee_rates()

    # Print human-readable summary
    PSBTReport.print_summary(psbt_info, recommended_fee_rates)
