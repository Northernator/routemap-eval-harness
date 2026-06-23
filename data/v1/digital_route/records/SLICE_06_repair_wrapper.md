# Phase 3 Slice 6 - Repair Wrapper

Date: 2026-06-23

## Purpose

Turn sound detection into an improvement loop: detect, diagnose, repair, re-extract, and re-verify while preserving the one-sided checker caveat.

## Files created

- `src/dr_repair_wrapper_v1.py`
- `src/dr_run_repair_eval_v1.py`
- `data/v1/digital_route/slice_06_repair/repair_cache.jsonl`
- `data/v1/digital_route/slice_06_repair/repair_results.csv`
- `data/v1/digital_route/slice_06_repair/repair_summary.csv`
- `data/v1/digital_route/slice_06_repair/repair_summary.json`
- `data/v1/digital_route/slice_06_repair/repair_spot_check.csv`
- `data/v1/digital_route/records/SLICE_06_repair_wrapper.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_run_repair_eval_v1.py --rounds 2`
- `python -m py_compile src/dr_repair_wrapper_v1.py src/dr_run_repair_eval_v1.py`
- `git -C . diff --check`

## Per-Domain Results

| Domain | Flagged | Checker pass | Actual correct | Pass-but-wrong | Residual | Before error | After flagged error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| arithmetic | 30 | 0.000 | 0.000 | 0 | 30 | 1.000 | 1.000 |
| python_code | 0 | 0.000 | 0.000 | 0 | 0 | 0.000 | 0.000 |
| json_schema | 18 | 0.444 | 0.444 | 0 | 10 | 0.600 | 0.556 |

## Soundness Guard

`NOT_RULED_OUT` after repair is reported only as checker pass, not correctness. Actual correctness is tracked separately where available: arithmetic exact value, JSON schema validity, and Python parseability only. The `passes_but_wrong` column measures repaired outputs that pass the checker but still fail the available truth/property check.

## Spot-Check Notes

Exported 48 repaired cases with original output, diagnostic, repaired output, final verdict, and actual-correct flag.

## Conclusion

Repair effectiveness is domain-specific. JSON schema violations are expected to be repairable from targeted diagnostics; hard arithmetic may remain weak because the model must recompute, not just satisfy a local structural constraint.

## Next Slice

Add a two-stage repair policy that routes arithmetic repairs to structured scratchpad generation plus residue self-check, while keeping JSON/code repairs terse and schema-directed.
