"""
Bitcoin transaction data structure classes
"""
import json
from pydantic import BaseModel, Field, model_validator

class TXWitnessStackItem(BaseModel):
    stack_item_size: int = Field(ge=0)
    stack_item: bytes

    @model_validator(mode='after')
    def check_size_matches(self):
        if len(self.stack_item) != self.stack_item_size:
            raise ValueError(f'stack_item length {len(self.stack_item)} != stack_item_size {self.stack_item_size}')
        return self

    def to_string(self):
        return json.dumps({
            "stack_item_size": self.stack_item_size,
            "stack_item": self.stack_item.hex()
        }, indent=2)

class TXWitnessStack(BaseModel):
    witness_items: list['TXWitnessStackItem']

    def to_string(self):
        return json.dumps({
            "witness_items": [json.loads(item.to_string()) for item in self.witness_items]
        }, indent=2)

class TXInput(BaseModel):
    txid: bytes = Field(min_length=32, max_length=32)  # Transaction ID is always 32 bytes
    vout: bytes = Field(min_length=4, max_length=4)    # Output index is 4 bytes
    ss_size: int = Field(ge=0)                          # ScriptSig size
    ss: bytes                                           # ScriptSig
    seq: bytes = Field(min_length=4, max_length=4)     # Sequence is 4 bytes

    @model_validator(mode='after')
    def check_size_matches(self):
        if len(self.ss) != self.ss_size:
            raise ValueError(f'ss length {len(self.ss)} != ss_size {self.ss_size}')
        return self

    def to_string(self):
        return json.dumps({
            "txid": self.txid.hex(),
            "vout": self.vout.hex(),
            "ss_size": self.ss_size,
            "ss": self.ss.hex(),
            "seq": self.seq.hex()
        }, indent=2)

class TXOutput(BaseModel):
    amount: int = Field(ge=0)       # Amount in satoshis, must be non-negative
    spk_size: int = Field(ge=0)     # ScriptPubKey size
    spk: bytes                      # ScriptPubKey

    @model_validator(mode='after')
    def check_size_matches(self):
        if len(self.spk) != self.spk_size:
            raise ValueError(f'spk length {len(self.spk)} != spk_size {self.spk_size}')
        return self

    def to_string(self):
        return json.dumps({
            "amount": self.amount,
            "spk_size": self.spk_size,
            "spk": self.spk.hex()
        }, indent=2)

class Transaction(BaseModel):
    version: bytes = Field(min_length=4, max_length=4)  # Version is 4 bytes
    witness_flag: int = Field(ge=0, le=1)                # 0 or 1
    inputs: list[TXInput]
    outputs: list[TXOutput]
    witness: list                                        # Witness data
    locktime: bytes = Field(min_length=4, max_length=4)  # Locktime is 4 bytes
    vbytes: float = Field(gt=0)                          # Virtual bytes, must be positive

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
