"""
Bitcoin transaction data structure classes
"""
import json

class Transaction:
    def __init__(self, version: int, witness_flag: int, inputs: list, outputs: list, witness, locktime: int, vbytes: float):
        self.version = version
        self.witness_flag = witness_flag
        self.inputs = inputs
        self.outputs = outputs
        self.witness = witness
        self.locktime = locktime
        self.vbytes = vbytes

    def to_string(self):
        return json.dumps({
            "version": self.version.hex(),
            "witness_flag": self.witness_flag,
            "inputs": [json.loads(inp.to_string()) for inp in self.inputs],
            "outputs": [json.loads(out.to_string()) for out in self.outputs],
            "witness": self.witness,
            "locktime": self.locktime.hex(),
            "vbytes": self.vbytes
        }, indent=2)

    def get_input_count(self):
        return len(self.inputs)

    def get_output_count(self):
        return len(self.outputs)

class TXInput:
    def __init__(self, txid: bytes, vout: bytes, ss_size: int, ss: bytes, seq: bytes):
        self.txid = txid
        self.vout = vout
        self.ss_size = ss_size
        self.ss = ss
        self.seq = seq

    def to_string(self):
        return json.dumps({
            "txid": self.txid.hex(),
            "vout": self.vout.hex(),
            "ss_size": self.ss_size,
            "ss": self.ss.hex(),
            "seq": self.seq.hex()
        }, indent=2)

class TXOutput:
    def __init__(self, amount: int, spk_size: int, spk: bytes):
        self.amount = amount
        self.spk_size = spk_size
        self.spk = spk

    def to_string(self):
        return json.dumps({
            "amount": self.amount,
            "spk_size": self.spk_size,
            "spk": self.spk.hex()
        }, indent=2)

class TXWitnessStack:
    def __init__(self, witness_items: list):
        self.witness_items = witness_items

    def to_string(self):
        return json.dumps({
            "witness_items": [json.loads(item.to_string()) for item in self.witness_items]
        }, indent=2)

class TXWitnessStackItem:
    def __init__(self, stack_item_size: int, stack_item: bytes):
        self.stack_item_size = stack_item_size
        self.stack_item = stack_item

    def to_string(self):
        return json.dumps({
            "stack_item_size": self.stack_item_size,
            "stack_item": self.stack_item.hex()
        }, indent=2)
