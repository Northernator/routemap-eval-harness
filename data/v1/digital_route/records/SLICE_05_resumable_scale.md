# Phase 3 Slice 5 - Resumable Generation and Offline Scale

Date: 2026-06-23

## Purpose

Decouple local llama generation from checker evaluation. Generation is resumable, token-capped, and cached; evaluation is offline and cannot time out on Ollama.

## Files created

- `src/dr_generate_corpus_v1.py`
- `src/dr_run_checker_framework_eval_v3.py`
- `data/v1/digital_route/slice_05_scale/corpus.jsonl`
- `data/v1/digital_route/slice_05_scale/results.csv`
- `data/v1/digital_route/slice_05_scale/summary.csv`
- `data/v1/digital_route/slice_05_scale/summary.json`
- `data/v1/digital_route/slice_05_scale/spot_check_ruleouts.csv`
- `data/v1/digital_route/records/SLICE_05_resumable_scale.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_generate_corpus_v1.py --domain all --n 30 --timeout 60 --retries 2 --out data/v1/digital_route/slice_05_scale/corpus.jsonl`
- `python src/dr_run_checker_framework_eval_v3.py --cache data/v1/digital_route/slice_05_scale/corpus.jsonl`
- `python -m py_compile src/dr_generate_corpus_v1.py src/dr_run_checker_framework_eval_v3.py`
- `git -C . diff --check`

## Per-Domain Results

| Domain | Completed | Completed rate | Extraction success | Rule-out | UNCHECKABLE | Practical FP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| arithmetic | 30/30 | 1.000 | 0.867 | 1.000 | 0.133 | 0.000 |
| python_code | 30/30 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| json_schema | 30/30 | 1.000 | 1.000 | 0.600 | 0.000 | 0.000 |

## Spot-Check Notes

Spot-check rows exported: arithmetic 15, python_code 0, json_schema 15. Each row includes raw output, extracted content, and checker reason. Fewer than 15 rows means fewer than 15 rule-outs were observed for that domain.

## Arithmetic Anchor

Arithmetic still uses the Slice 1 residue adapter. Offline evaluation compares extracted integers with known bignum truth and preserves the Slice 2 one-sided contract: residue disagreement may rule out, but agreement never means correct.

## Conclusion

The resumable cache makes generation failures local to individual task IDs, and the offline evaluator turns generation or extraction failures into `UNCHECKABLE` rather than false rule-outs. Practical false-positive rate was 0.000 in every domain.

## Next Slice

Build the repair wrapper: feed `RULED_OUT_WRONG` and `UNCHECKABLE` outputs back to the model with terse, checker-specific diagnostics and measure repair success.
