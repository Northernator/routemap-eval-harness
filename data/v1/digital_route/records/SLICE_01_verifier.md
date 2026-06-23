# Phase 3 Slice 1 - Digital Route Verifier

Date: 2026-06-22

## Purpose

Build an exact modular-arithmetic wrong-answer detector beside LLM arithmetic. The verifier is one-sided and sound: residue disagreement proves a claimed answer is wrong; residue agreement only returns `NOT_RULED_OUT`.

## Files created

- `src/dr_residue_engine_v1.py`
- `src/dr_verifier_v1.py`
- `src/dr_run_verifier_benchmark_v1.py`
- `data/v1/digital_route/slice_01_verifier/verifier_results.csv`
- `data/v1/digital_route/slice_01_verifier/catch_rates.csv`
- `data/v1/digital_route/slice_01_verifier/compute_saved.csv`
- `data/v1/digital_route/records/SLICE_01_verifier.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_run_verifier_benchmark_v1.py` -> passed
- `python -m py_compile src/dr_residue_engine_v1.py src/dr_verifier_v1.py src/dr_run_verifier_benchmark_v1.py` -> passed
- `git -C . diff --check` -> passed

## Results

False-positive rate on correct answers: 0.000

| Corruption type | Wrong answers | Ruled out | Catch rate |
| --- | ---: | ---: | ---: |
| random_offset | 11 | 11 | 1.000 |
| digit_transpose | 11 | 11 | 1.000 |
| off_by_power10 | 11 | 11 | 1.000 |
| sign_flip | 11 | 11 | 1.000 |
| off_by_multiple_of_9 | 11 | 11 | 1.000 |
| overall | 55 | 55 | 1.000 |

## Compute Saved

| Problem | Family | Digits est. | Residue sec | Full sec | Full/residue | Status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| power_small | power | 9 | 0.000006800 | 0.000002500 | 0.4 | measured |
| power_medium | power | 393 | 0.000024300 | 0.000006200 | 0.3 | measured |
| power_large | power | 25458 | 0.000008400 | 0.001349100 | 160.6 | measured |
| factorial_small | factorial | 26 | 0.000009300 | 0.000002000 | 0.2 | measured |
| factorial_medium | factorial | 110 | 0.000010700 | 0.000003000 | 0.3 | measured |
| factorial_edge | factorial | 158 | 0.000012900 | 0.000004600 | 0.4 | measured |
| fibonacci_small | fibonacci | 9 | 0.000017200 | 0.000003500 | 0.2 | measured |
| fibonacci_medium | fibonacci | 209 | 0.000025300 | 0.000008900 | 0.4 | measured |
| fibonacci_large | fibonacci | 4180 | 0.000034000 | 0.000175800 | 5.2 | measured |
| bigsum_medium | bigsum | 24 | 0.001241900 | 0.000108200 | 0.1 | measured |
| bigprod_medium | bigprod | 927 | 0.000233300 | 0.000054200 | 0.2 | measured |
| power_extreme_skip | power | 9999922 | 0.000009100 |  |  | skipped_impractical |
| factorial_extreme_skip | factorial | 456574 | 0.000005000 |  |  | skipped_impractical |
| fibonacci_extreme | fibonacci | 104494 | 0.000047800 | 0.027522800 | 575.8 | measured |
| bigsum_large | bigsum | 11 | 0.216267200 | 0.024999000 | 0.1 | measured |

Full expansion was skipped as impractical when estimated decimal digits exceeded 250,000.

## LLM Pass

Skipped; `--with-llm` was not requested.

## Diagnosis

Cheap residue routing reliably rules out wrong arithmetic with zero false positives in this benchmark. `off_by_multiple_of_9` evades the mod-9/digital-root component, but the other coprime moduli still catch it unless the error is a multiple of the combined modulus `33666633`. Any wrong answer differing from truth by a multiple of that full product remains a blind spot and returns `NOT_RULED_OUT`, not `correct`.

## Conclusion

The Digital Route verifier gives a small, exact arithmetic conscience for LLM outputs: fast modular routes catch most wrong answers while preserving the sound one-sided contract.

## Next Slice

Add structured expression parsing for LLM-produced arithmetic traces, then verify intermediate steps rather than only final answers.
