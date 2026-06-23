# Phase 3 Slice 2 - Real Model Verification and Benchmark Hardening

Date: 2026-06-22

## Purpose

Demonstrate that the Slice 1 Digital Route verifier catches real llama 3.1 arithmetic errors, then harden the synthetic benchmark with larger N, an empirical combined-modulus blind spot, and modulus-bank sensitivity.

## Files created

- `src/dr_run_llm_verification_v2.py`
- `src/dr_run_benchmark_hardening_v2.py`
- `data/v1/digital_route/slice_02_real_model/llm_raw_outputs_limit_5.jsonl`
- `data/v1/digital_route/slice_02_real_model/llm_results_limit_5.csv`
- `data/v1/digital_route/slice_02_real_model/llm_summary_limit_5.json`
- `data/v1/digital_route/slice_02_real_model/llm_raw_outputs_full.jsonl`
- `data/v1/digital_route/slice_02_real_model/llm_results_full.csv`
- `data/v1/digital_route/slice_02_real_model/llm_summary_full.json`
- `data/v1/digital_route/slice_02_hardening/hardening_results.csv`
- `data/v1/digital_route/slice_02_hardening/hardening_summary.json`
- `data/v1/digital_route/slice_02_hardening/bank_sensitivity.csv`
- `data/v1/digital_route/slice_02_hardening/bank_sensitivity_summary.json`
- `data/v1/digital_route/records/SLICE_02_real_model_and_hardening.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_run_llm_verification_v2.py --limit 5` -> passed
- `python src/dr_run_llm_verification_v2.py` -> passed
- `python src/dr_run_benchmark_hardening_v2.py` -> passed
- `python -m py_compile src/dr_run_llm_verification_v2.py src/dr_run_benchmark_hardening_v2.py` -> passed
- `git -C . diff --check` -> passed

## Real llama 3.1 Verification

Parsed 32 of 32 model answers; parse failures 0; arithmetic error rate 0.844; verifier catch rate on real errors 1.000; false-positive rate 0.000; missed errors: none. The exact/residue verification timing ratio was 0.098 on this small mixed battery, meaning exact bignum recomputation was faster here, while residue routing remains bounded and diagnostic for the larger synthetic families.

## Synthetic Hardening

Synthetic problems: 250

Standard corruption catch rate: 1.000

All wrong-answer catch rate including designed blind spot: 0.833

False-positive rate on correct answers: 0.000

| Corruption type | Wrong answers | Ruled out | Catch rate | Escapes multiples of M |
| --- | ---: | ---: | ---: | --- |
| digit_transpose | 250 | 250 | 1.000 | True |
| off_by_combined_modulus | 250 | 0 | 0.000 | True |
| off_by_multiple_of_9 | 250 | 250 | 1.000 | True |
| off_by_power10 | 250 | 250 | 1.000 | True |
| random_offset | 250 | 250 | 1.000 | True |
| sign_flip | 250 | 250 | 1.000 | True |

## Blind-Spot Demonstration

`off_by_combined_modulus` adds exact multiples of M = `33666633`. Catch rate is 0.000; these wrong answers return `NOT_RULED_OUT`, never `correct`.

## Bank Sensitivity

| Bank | M | Random errors | Ruled out | Escaped | Catch rate | Escapes multiples of M |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| digital_root_only | 9 | 200000 | 177800 | 22200 | 0.889000 | 1 |
| small_7_9_11 | 693 | 200000 | 199720 | 280 | 0.998600 | 1 |
| default_7_9_11_13_37_101 | 33666633 | 200000 | 200000 | 0 | 1.000000 | 1 |
| extended_default_41_43 | 59354273979 | 200000 | 200000 | 0 | 1.000000 | 1 |

## Conclusion

The verifier catches real parsed llama 3.1 arithmetic errors at zero false positives in this run. Synthetic hardening reconfirms the sound one-sided contract at N >= 200 and empirically isolates the only designed miss class: errors that are multiples of the active bank's combined modulus.

## Next Slice

Build a verifier-wrapper attach point that intercepts model arithmetic answers, emits residue diagnostics, and asks the model to repair only answers ruled out by the verifier.
