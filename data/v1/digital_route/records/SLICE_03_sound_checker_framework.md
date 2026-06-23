# Phase 3 Slice 3 - Sound Checker Framework

Date: 2026-06-22

## Purpose

Generalize Digital Route arithmetic verification into a routed library of cheap sound checkers. Each checker returns only `RULED_OUT_WRONG` or `NOT_RULED_OUT`, preserves zero false positives on known-valid outputs, and documents its blind spot.

## Files created

- `src/dr_checker_framework_v1.py`
- `src/dr_checker_code_v1.py`
- `src/dr_checker_schema_v1.py`
- `src/dr_run_checker_framework_eval_v1.py`
- `data/v1/digital_route/slice_03_framework/raw_outputs_limit_5.jsonl`
- `data/v1/digital_route/slice_03_framework/framework_results_limit_5.csv`
- `data/v1/digital_route/slice_03_framework/framework_summary_limit_5.json`
- `data/v1/digital_route/slice_03_framework/raw_outputs_full.jsonl`
- `data/v1/digital_route/slice_03_framework/framework_results_full.csv`
- `data/v1/digital_route/slice_03_framework/framework_summary_full.json`
- `data/v1/digital_route/slice_03_framework/known_valid_fp_checks.csv`
- `data/v1/digital_route/slice_03_framework/coverage_report.csv`
- `data/v1/digital_route/records/SLICE_03_sound_checker_framework.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_run_checker_framework_eval_v1.py --limit 5` -> passed
- `python src/dr_run_checker_framework_eval_v1.py` -> passed
- `python -m py_compile src/dr_checker_framework_v1.py src/dr_checker_code_v1.py src/dr_checker_schema_v1.py src/dr_run_checker_framework_eval_v1.py` -> passed
- `git -C . diff --check` -> passed

## Per-Domain Results

| Domain | Model outputs | Ruled out | Checkable error rate | Known-valid FP rate |
| --- | ---: | ---: | ---: | ---: |
| arithmetic | 5 | 5 | 1.000 | 0.000 |
| json_schema | 5 | 5 | 1.000 | 0.000 |
| python_code | 5 | 5 | 1.000 | 0.000 |

## Coverage Characterization

| Checker | Coverage | Blind-spot example |
| --- | --- | --- |
| arithmetic_residue_v1 | Catches arithmetic answers whose difference from truth is nonzero modulo at least one active modulus; cannot catch errors that are multiples of the combined modulus. | For 2 + 3, claimed 33666638 passes the default bank because it differs from 5 by M=33666633. |
| python_code_parse_v1 | Catches syntactically impossible Python; cannot catch code that parses but computes the wrong result. | def add(a, b):<br>    return a - b |
| json_schema_constraints_v1 | Catches invalid JSON and declared type/required/enum/range violations; cannot catch schema-valid but semantically wrong values. | {"answer": 42, "units": "meters"} can satisfy a schema even when the real answer is 43 meters. |

## Arithmetic Anchor

Arithmetic uses the Slice 1 residue verifier adapter. Framework verdicts preserve the Slice 2 one-sided behavior: arithmetic outputs are ruled out only by residue disagreement, and known-valid arithmetic outputs had FP = 0.000.

## Conclusion

The sound-checker pattern generalizes across arithmetic, Python parse checking, and JSON schema constraints while preserving the zero-false-positive guarantee on constructed valid outputs. Each checker has an explicit blind spot: residue multiples of M, parseable-but-wrong code, or schema-valid-but-semantically-wrong JSON.

## Next Slice

Add a repair/wrapper action layer that routes model outputs through sound checkers, emits targeted diagnostics, and asks the model to repair only outputs that are ruled out.
