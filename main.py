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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <filename>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        hex_string = f.read().strip()

    byte_data = bytes.fromhex(hex_string)
    buffer = BytesIO(byte_data)

    # Parse PSBT
    psbt = PSBTParser.parse_psbt(buffer)
    print(psbt.to_string())

    # Parse PSBT info
    psbt_info = PSBTInfoParser.get_info(psbt)
    print(psbt_info.to_string())

    # Get recommended fee rate from mempool
    mempool = MempoolAPI()
    recommended_fee_rate = mempool.get_recommended_fee_rate()

    if recommended_fee_rate:
        minimum_fee_rate = recommended_fee_rate.get("minimumFee", 0)
        print("Minimum fee rate: " + str(minimum_fee_rate))

        if psbt_info.fee_rate < minimum_fee_rate:
            print("Fee rate is below minimum fee rate")
        else:
            print("Fee rate is above minimum fee rate")
    else:
        print("Could not fetch recommended fee rate from mempool API")

#TO-DO
# parse PSBT_IN_WITNESS_UTXO to get amount etc
# parse PSBT_IN_WITNESS_SCRIPT to determine script type
# parse PSBT_IN_PREVIOUS_TXID and PSBT_IN_OUTPUT_INDEX to get previous transaction and output index
# parse PSBT_OUT_AMOUNT and PSBT_OUT_SCRIPT to get amount and script
# add new helper class to make RPC calls to some mempool node to get the transaction details


#V0 single
#PSBT_IN_NON_WITNESS_UTXO
#PSBT_IN_WITNESS_UTXO

#1. for each input key:
#   a. if PSBT_IN_NON_WITNESS_UTXO, use transaction outpoint to get amount and add to total (and verify amount from PSBT_IN_WITNESS_UTXO)
#   b. else if PSBT_IN_WITNESS_UTXO, add amount to total
#2. sum output amounts from transaction
#3. subtract outputs from inputs to get fee

#v0 multi
#PSBT_IN_NON_WITNESS_UTXO
#PSBT_IN_WITNESS_UTXO
#PSBT_IN_WITNESS_SCRIPT
#PSBT_IN_BIP32_DERIVATION

# same as v0 single 

#v2 single
#PSBT_IN_WITNESS_UTXO
#PSBT_IN_PREVIOUS_TXID
#PSBT_IN_OUTPUT_INDEX
#PSBT_OUT_AMOUNT
#PSBT_OUT_SCRIPT

# 1. for each input key, sum amounts from PSBT_IN_WITNESS_UTXO
# 2. for each output key, sum PSBT_OUT_AMOUNT
# 3. subtract outputs from inputs to get fee

#V2 multi
#PSBT_IN_NON_WITNESS_UTXO
#PSBT_IN_REDEEM_SCRIPT
#PSBT_IN_BIP32_DERIVATION
#PSBT_IN_BIP32_DERIVATION
#PSBT_IN_PREVIOUS_TXID
#PSBT_IN_OUTPUT_INDEX
#PSBT_OUT_AMOUNT
#PSBT_OUT_SCRIPT

#1. for each input key, use PSBT_IN_OUTPUT_INDEX to grab amount from PSBT_IN_NON_WITNESS_UTXO. sum amounts.
#2. for each output key, sum PSBT_OUT_AMOUNT
#3. subtract outputs from inputs to get fee