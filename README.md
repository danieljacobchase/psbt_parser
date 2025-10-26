# PSBT Parser

A Python-based Bitcoin PSBT (Partially Signed Bitcoin Transaction) parser and analyzer supporting both BIP-174 (v0) and BIP-370 (v2) standards.

## What are PSBTs?

**Partially Signed Bitcoin Transactions (PSBTs)** are a standardized format for Bitcoin transactions that aren't yet fully signed. They enable:

- **Multi-party signing workflows**: Multiple participants can add signatures independently
- **Hardware wallet compatibility**: Standardized format for offline signing devices
- **Air-gapped security**: Transactions can move between online and offline systems
- **Transparency**: All parties can inspect transaction details before signing

PSBTs move through workflow stages:
1. **Creator** - Constructs the initial unsigned transaction
2. **Constructor** (v2) - Adds inputs and outputs
3. **Updater** - Adds UTXO information and scripts
4. **Signer** - Adds signatures (multiple signers for multisig)
5. **Combiner** - Merges signatures from multiple signers
6. **Finalizer** - Creates final scriptSig/scriptWitness
7. **Extractor** - Produces the final signed transaction for broadcast

### Supported Standards

- **BIP-174**: PSBT Version 0 (original specification)
- **BIP-370**: PSBT Version 2 (adds constructor role, modular fields)

## Features

- ✅ Parse PSBT v0 and v2 transactions from hex or binary format
- ✅ Extract transaction details (inputs, outputs, amounts)
- ✅ Identify script types (P2PKH, P2SH, P2WPKH, P2WSH, P2TR)
- ✅ Calculate transaction fees and fee rates (sat/vB)
- ✅ Detect change outputs via BIP32 derivation paths
- ✅ Compare fees against real-time mempool data
- ✅ Support for both legacy and SegWit transactions
- ✅ Handle multi-signature workflows

## Project Organization

```
psbt_parser/
├── main.py                    # CLI entry point
├── psbt_report.py            # Human-readable output formatting
├── models/                   # Data structure definitions
│   ├── constants.py          # Bitcoin constants & PSBT key type mappings
│   ├── keys.py              # PSBT key-specific models
│   ├── psbt.py              # PSBT data structures
│   └── transaction.py       # Bitcoin transaction models
├── parser/                   # Parsing logic
│   ├── parser_utils.py      # Utility functions (compact size, buffer ops)
│   ├── psbt_parser.py       # Main PSBT parser (BIP-174/370)
│   ├── transaction_parser.py # Bitcoin transaction parser
│   ├── psbt_key_parser.py   # Specialized PSBT key parsers
│   └── psbt_info_parser.py  # High-level PSBT information extraction
├── api/                      # External API clients
│   └── mempool.py           # Mempool.space fee rate API
└── sample_data/             # Sample PSBT files (22 test cases)
    ├── raw/                 # Hex-encoded PSBT files
    │   ├── v0_p2wpkh_*.txt      # PSBT v0 single-sig workflow
    │   ├── v0_multisig_*.txt    # PSBT v0 multisig (2-of-2) workflow
    │   ├── v2_p2wpkh_*.txt      # PSBT v2 single-sig workflow
    │   └── v2_multisig_*.txt    # PSBT v2 multisig workflow
    └── psbt/                # Binary PSBT files
        └── *.psbt
```

### Architecture

- **models/** - Pure data structures with no business logic
- **parser/** - Stateless parsing functions following BIP specifications
- **api/** - External service integrations (mempool data)
- **sample_data/** - Real PSBT examples at different workflow stages

## Prerequisites

- **Python 3.11+** (uses modern type hint syntax)
- **No external dependencies** - uses only Python standard library

## Running the Parser

### Basic Usage

Parse and analyze a PSBT file (supports both hex-encoded and binary formats):

```bash
# Hex-encoded PSBT (.txt)
python main.py sample_data/raw/v0_p2wpkh_3_finalizer.txt

# Binary PSBT (.psbt)
python main.py sample_data/psbt/v0_p2wpkh_3_finalizer.psbt
```

### Input Format

The parser accepts two input formats:

**Hex-encoded text files** (.txt):
```
70736274ff01005...  # PSBT in hexadecimal format
```

**Binary PSBT files** (.psbt):
```
Raw binary PSBT data
```

### Example Output

```
============================================================
PSBT SUMMARY
============================================================

PSBT Version: 0

Inputs (1):
  [0] 30,000 sats | Native SegWit (bech32) | P2WPKH

Outputs (1):
  [0] 25,000 sats | Native SegWit (bech32) | P2WPKH

Transaction Summary:
  Total Input:      30,000 sats
  Total Output:     25,000 sats
  Transaction Size: ~82.0 vB
  Fee:              5,000 sats
  Fee Rate:         ~61 sat/vB
  Assessment:       Fee rate is excessive/wasteful

Recommended Fee Rates (mempool.space):
  Fastest (<10 min):  3 sat/vB
  Half Hour:          1 sat/vB
  One Hour:           1 sat/vB
  Economy:            1 sat/vB
  Minimum:            1 sat/vB

============================================================
```

### Handling Different PSBT Stages

**Early-stage PSBTs** (creator/constructor without UTXO data):
```bash
python main.py sample_data/raw/v2_p2wpkh_0_creator.txt
```
Output:
```
Note: This PSBT is at an early stage (creator/constructor) and lacks
      UTXO data needed for amount and fee analysis.

PSBT Version: 2
Inputs: 0
Outputs: 0
```

**Fully-signed PSBTs** (finalizer stage):
```bash
python main.py sample_data/raw/v0_multisig_5_finalizer.txt
```

## Running Tests

### Prerequisites

Install pytest:

```bash
pip install pytest
```

### Run All Tests

Execute the full test suite (133 tests):

```bash
pytest tests/ -v
```

### Run Specific Test Files

Test individual parser modules:

```bash
# Test parsing utilities
pytest tests/test_parser_utils.py -v

# Test transaction parsing
pytest tests/test_transaction_parser.py -v

# Test PSBT parsing
pytest tests/test_psbt_parser.py -v

# Test key parsing
pytest tests/test_psbt_key_parser.py -v

# Test info extraction
pytest tests/test_psbt_info_parser.py -v
```

### Run Tests with Coverage

Install coverage tools:

```bash
pip install pytest-cov
```

Run with coverage report:

```bash
pytest tests/ --cov=parser --cov=models --cov=api --cov-report=term-missing
```

### Test Organization

```
tests/
├── test_parser_utils.py        # 30 tests - utility function tests
├── test_transaction_parser.py  # 29 tests - transaction parsing tests
├── test_psbt_parser.py         # 38 tests - PSBT format parsing tests
├── test_psbt_key_parser.py     # 26 tests - PSBT key data parsing tests
└── test_psbt_info_parser.py    # 26 tests - high-level info extraction tests
```

All tests are **unit tests** that verify function-level behavior with crafted inputs, covering:
- Normal cases
- Edge cases (empty data, zero values, maximum values)
- Error conditions (invalid formats, missing data)
- Bitcoin-specific scenarios (SegWit detection, script type identification)

## Example Workflows

### Analyzing a Single-Sig Transaction

```bash
# Parse a finalizer-stage PSBT (ready to broadcast) - hex format
python main.py sample_data/raw/v0_p2wpkh_3_finalizer.txt
```

### Analyzing a Multisig Transaction

```bash
# Parse a 2-of-2 multisig PSBT after both signatures - binary format
python main.py sample_data/psbt/v0_multisig_5_finalizer.psbt
```

### Comparing v0 vs v2 Formats

```bash
# PSBT v0 format
python main.py sample_data/raw/v0_p2wpkh_3_finalizer.txt

# PSBT v2 format
python main.py sample_data/raw/v2_p2wpkh_4_finalizer.txt
```

## Implementation Details

### Parsing Approach

- **Stateless parsers**: All parsing functions are pure, taking buffers and returning data structures
- **BIP-compliant**: Strictly follows BIP-174 and BIP-370 specifications
- **Error handling**: Gracefully handles early-stage PSBTs and invalid formats
- **Type safety**: Extensive use of type hints for better code clarity

### Script Type Detection

The parser identifies these Bitcoin script types:

| Script Type | Description | Address Format |
|-------------|-------------|----------------|
| P2PKH | Pay-to-Public-Key-Hash (legacy) | Base58 (1...) |
| P2SH | Pay-to-Script-Hash | Base58 (3...) |
| P2WPKH | Pay-to-Witness-Public-Key-Hash | Bech32 (bc1q...) |
| P2WSH | Pay-to-Witness-Script-Hash | Bech32 (bc1q...) |
| P2TR | Pay-to-Taproot | Bech32m (bc1p...) |

### Fee Rate Assessment

Fee rates are compared against mempool.space data:

- **Too Low**: < 50% of slow rate (may not confirm)
- **Slow**: 50-100% of slow rate (~1 hour)
- **Normal**: Between slow and fast (~30 min)
- **Fast**: >= fast rate (next block)
- **Excessive**: > 2x fast rate (overpaying)

## Limitations

- **No signature creation**: This is a parser/analyzer only, not a signer
- **Read-only**: Does not modify or create PSBTs
- **Single transaction**: Processes one PSBT at a time
- **Network dependency**: Fee rate comparison requires internet connection

## References

- [BIP-174: Partially Signed Bitcoin Transaction Format](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki)
- [BIP-370: PSBT Version 2](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki)
- [BIP-32: Hierarchical Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)

## License

MIT
