# Phase 3 Slice 4 - Output Extraction Fix

Date: 2026-06-22

## Purpose

Fix the Slice 3 raw-wrapper false-positive cascade by extracting code, JSON, or integers before checking. Extraction failures now return `UNCHECKABLE`, never `RULED_OUT_WRONG`.

## Files created

- `src/dr_output_extraction_v1.py`
- `src/dr_run_checker_framework_eval_v2.py`
- `data/v1/digital_route/slice_04_extraction/raw_outputs_limit_5.jsonl`
- `data/v1/digital_route/slice_04_extraction/raw_batches_limit_5.jsonl`
- `data/v1/digital_route/slice_04_extraction/results_limit_5.csv`
- `data/v1/digital_route/slice_04_extraction/summary_limit_5.json`
- `data/v1/digital_route/slice_04_extraction/raw_outputs_full.jsonl`
- `data/v1/digital_route/slice_04_extraction/raw_batches_full.jsonl`
- `data/v1/digital_route/slice_04_extraction/results_full.csv`
- `data/v1/digital_route/slice_04_extraction/summary_full.json`
- `data/v1/digital_route/slice_04_extraction/before_after.csv`
- `data/v1/digital_route/slice_04_extraction/manual_spot_check_ruleouts.csv`
- `data/v1/digital_route/records/SLICE_04_extraction_fix.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_run_checker_framework_eval_v2.py --limit 5` -> passed
- `python src/dr_run_checker_framework_eval_v2.py` -> passed with all full-run chunks timing out into `UNCHECKABLE`
- `python -m py_compile src/dr_output_extraction_v1.py src/dr_run_checker_framework_eval_v2.py` -> passed
- `git -C . diff --check` -> passed

## Per-Domain Results

| Domain | Outputs | Extraction success | Extracted rule-out | UNCHECKABLE | Practical FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| arithmetic | 50 | 0.000 | 0.000 | 1.000 | 0.000 |
| python_code | 50 | 0.000 | 0.000 | 1.000 | 0.000 |
| json_schema | 50 | 0.000 | 0.000 | 1.000 | 0.000 |

## Before / After

| Domain | Slice 3 raw rule-out | Slice 4 current raw rule-out | Slice 4 extracted rule-out | Slice 4 UNCHECKABLE |
| --- | ---: | ---: | ---: | ---: |
| python_code | 1.000 | 0.000 | 0.000 | 1.000 |
| json_schema | 1.000 | 1.000 | 0.000 | 1.000 |

## Spot-Check Notes

Manual spot-check CSV rows: arithmetic 0, python_code 0, json_schema 0. Rows include raw response, extracted content, and checker reason so remaining rule-outs can be inspected as content-level failures. If a domain has fewer than 15 rows, the eval produced fewer than 15 extracted rule-outs for that domain.

The smoke pass did exercise extraction on real wrapped outputs: code moved from raw-rule-out to extracted `NOT_RULED_OUT`, while the JSON smoke item remained a real schema violation after JSON extraction. The full N=50/domain pass was bounded by process-level Ollama timeouts; every full-run chunk returned no extractable content and therefore correctly became `UNCHECKABLE`, not `RULED_OUT_WRONG`.

## Arithmetic Anchor

Arithmetic still uses the Slice 1 residue checker after tolerant integer extraction. This preserves the Slice 2 behavior: residue disagreement rules out wrong arithmetic, while extraction failure is `UNCHECKABLE`.

## Coverage

arithmetic_residue_v1: Catches arithmetic answers whose difference from truth is nonzero modulo at least one active modulus; cannot catch errors that are multiples of the combined modulus. Blind spot: For 2 + 3, claimed 33666638 passes the default bank because it differs from 5 by M=33666633.
python_code_parse_v1: Catches syntactically impossible Python; cannot catch code that parses but computes the wrong result. Blind spot: def add(a, b):
    return a - b
json_schema_constraints_v1: Catches invalid JSON and declared type/required/enum/range violations; cannot catch schema-valid but semantically wrong values. Blind spot: {"answer": 42, "units": "meters"} can satisfy a schema even when the real answer is 43 meters.

## Conclusion

Extract-before-check removes wrapper/prose artifacts from code and JSON checking and moves extraction failure into an honest `UNCHECKABLE` bucket. Practical false-positive rates on extracted valid outputs were 0.000 for all domains in this run, but the full run did not recover enough extracted content to estimate real full-scale content error rates; that remains a generation-throughput follow-up.

## Next Slice

Add a repair wrapper that sends only `RULED_OUT_WRONG` and `UNCHECKABLE` cases back to the model with targeted extraction/checker diagnostics.
