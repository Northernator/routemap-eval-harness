# HugeArithmeticRouteBench

Solver: `noisy`

Seed: `7`

N: `200`

Error mode: `off_by_M`

## Metrics

| Metric | Value |
| --- | ---: |
| raw_solver_accuracy | 0.550 |
| route_engine_accuracy | 1.000 |
| verifier_catch_rate | 1.000 |
| false_rejection_rate | 0.000 |
| blind_spot_rate | 0.000 |
| oracle_verifier_agreement | 1.000 |
| route_decidable_coverage | 0.875 |
| compute_saved_large | 4.522x |
| compute_saved_overall | 3.183x |
| full_expansion_impossible_cases | 81 |
| speed_bar_basis | expansion_impossible |
| verifier_minimum_bar | PASS |
| verifier_strong_bar | PASS |
| speed_minimum_bar | PASS |
| speed_strong_bar | PASS |

## Coverage Caveats

`impossibility` and `pascal_row_entry` tasks are predicate/verification-only in this slice and are counted honestly outside the route-answerable subset. CRT/cycle routes answer residues; they do not reconstruct full huge integers.

Catch rate is over residue-INCONSISTENT (catchable) wrong answers; residue-consistent errors are the characterized blind spot, reported separately. Speed bar basis is labelled.

## Methodology Guard

Ground truth is frozen in `tasks.jsonl` and computed by independent Python stdlib code in `routemap_bench.tasks`, not by `routemap_digital`.
