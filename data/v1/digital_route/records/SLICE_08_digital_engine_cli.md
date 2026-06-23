# Phase 3 Slice 8 - Digital Engine CLI

Date: 2026-06-23

## Purpose

Finish the named Digital Route engine layer by adding CRT reconstruction, cycle detection, expression parsing, and a CLI while preserving the existing residue/verifier modules as the single source of truth.

## Files created

- `src/routemap_digital/__init__.py`
- `src/routemap_digital/residue.py`
- `src/routemap_digital/verify.py`
- `src/routemap_digital/crt.py`
- `src/routemap_digital/cycles.py`
- `src/routemap_digital/parser.py`
- `src/routemap_digital/cli.py`
- `src/routemap_digital/__main__.py`
- `src/routemap_digital/README.md`
- `rd_test_digital_engine.py`
- `data/v1/digital_route/slice_08_digital_engine_cli/claim_wrong.json`
- `data/v1/digital_route/records/SLICE_08_digital_engine_cli.md`

## Design

`residue.py` re-exports `dr_residue_engine_v1`. `verify.py` re-exports `dr_verifier_v1`. New CRT and cycle helpers operate on residues around those modules and do not reimplement verifier logic.

CRT uses pairwise-coprime banks only. `crt_combine()` returns the unique representative in `[0, M)`. `reconstruct()` reports `ambiguous=False` only when a caller supplies `upper_bound <= M`; otherwise the result is only a value modulo `M`.

Cycle detection uses Brent's algorithm for deterministic finite states. `power_cycle()`, `pisano_period()`, and `linear_recurrence_period()` expose route-decidable periodic structure; `pow_mod_via_cycle()` and `fib_mod_via_cycle()` use those periods for residue answers.

## Honesty Guardrails

CRT reconstructs the integer only when it is provably less than or equal to `M`, the product of the bank. For huge expressions it yields the value mod `M`, not the original integer, and sets `ambiguous=True`. There is no lossless recovery of arbitrary numbers from residues.

Cycle detection answers residue and route-decidable questions. It does not reconstruct full values.

## CLI Transcript

```text
> python -m routemap_digital check "7^1000000 mod 9"
7^1000000 mod 9 = 7

> python -m routemap_digital verify --claim data/v1/digital_route/slice_08_digital_engine_cli/claim_wrong.json
{"disagreeing_moduli": [7], "verdict": "RULED_OUT_WRONG"}

> python -m routemap_digital verify --claim data/v1/digital_route/slice_08_digital_engine_cli/claim_wrong.json --strict
{"disagreeing_moduli": [7], "verdict": "RULED_OUT_WRONG"}
strict_exit=1
```

## Test Results

```text
python -m pytest rd_test_digital_engine.py -q
8 passed
```

## Index Note

`PHASE3_INDEX.md` was intentionally left unchanged to preserve the new-files-only constraint. Suggested index row:

`- 2026-06-23 - Slice 08: named digital engine with CRT, cycles, parser, and CLI; pytest 8 passed.`
