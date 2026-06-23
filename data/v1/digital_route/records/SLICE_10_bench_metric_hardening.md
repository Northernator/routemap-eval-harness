# Phase 3 Slice 10 - HugeArithmeticRouteBench Metric Hardening

Date: 2026-06-23

## Purpose

Harden Slice 09 benchmark metrics without changing the Digital Route engine. This slice fixes two methodology issues in `routemap_bench`.

## Fix 1 - Ground-Truth-Derived Blind/Catchable Classification

Before: `run_bench.run()` marked blind spots from solver intent (`NoisyEngineSolver(error="off_by_M")`).

After: `route.evaluate_task()` derives `catchable` and `blind_spot` from the ground-truth residue relationship for every solver:

- Integer route-checkable wrong rows:
  - `blind_spot = (claimed - ground_truth) % m == 0`
  - `catchable = (claimed - ground_truth) % m != 0`
- Boolean/predicate wrong rows are always catchable and never blind.

This works for oracle, noisy, cached, and optional ollama solvers because it depends on row data, not solver class.

## Fix 2 - Honest Speed Reporting

Before: `compute_saved` was a blended wall-clock ratio and speed bars passed silently through the full-expansion-impossible clause.

After:

- `compute_saved_overall`: retained blended ratio.
- `compute_saved_large`: ratio over feasible `size_class=="large"` rows.
- `compute_saved_by_size`: per-size ratios.
- `full_expansion_impossible_cases`: retained and surfaced.
- `speed_bar_basis`: one of `10x_large`, `expansion_impossible`, or `none`.

Speed bars now pass if `compute_saved_large` clears the threshold or if route-checkable full expansion is impossible; the card labels which basis applies.

## Metric Definitions

| Metric | Definition |
| --- | --- |
| `caught` | wrong and `verdict == "RULED_OUT_WRONG"` |
| `catchable` | wrong and residue-inconsistent with GT |
| `blind` | wrong and residue-consistent with GT |
| `verifier_catch_rate` | caught catchable rows / catchable rows |
| `blind_spot_rate` | caught blind rows / blind rows |
| `false_rejection_rate` | correct checked rows ruled out / correct checked rows |
| `oracle_verifier_agreement` | fraction of wrong route-checkable rows where `catchable == (verdict == "RULED_OUT_WRONG")` |

`oracle_verifier_agreement` must be 1.000. A lower value indicates a real verifier/metric bug.

## Offline Random-Error Card

| Metric | Value |
| --- | ---: |
| raw_solver_accuracy | 0.530 |
| route_engine_accuracy | 1.000 |
| verifier_catch_rate | 1.000 |
| false_rejection_rate | 0.000 |
| blind_spot_rate | 0.000 |
| oracle_verifier_agreement | 1.000 |
| route_decidable_coverage | 0.875 |
| compute_saved_large | 4.854x |
| compute_saved_overall | 3.278x |
| full_expansion_impossible_cases | 81 |
| speed_bar_basis | expansion_impossible |
| verifier_minimum_bar | PASS |
| verifier_strong_bar | PASS |
| speed_minimum_bar | PASS |
| speed_strong_bar | PASS |

## Offline Off-by-M Card

| Metric | Value |
| --- | ---: |
| raw_solver_accuracy | 0.550 |
| route_engine_accuracy | 1.000 |
| verifier_catch_rate | 1.000 |
| false_rejection_rate | 0.000 |
| blind_spot_rate | 0.000 |
| blind_spot_n | 55 |
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

The off-by-M run has 55 residue-consistent wrong integer rows. None were caught, so `blind_spot_rate=0.000`; these remain `NOT_RULED_OUT`, not false "correct" claims.

## Verification

```text
python -m pytest rb_test_bench.py -q
8 passed
```

## Index Note

`PHASE3_INDEX.md` was intentionally left unchanged to keep the working-tree scope to `routemap_bench`, generated Slice 09 cards, tests, and this new Slice 10 record. Suggested index row:

`- 2026-06-23 - Slice 10: HugeArithmeticRouteBench metrics hardened; GT-derived blind/catchable rows, oracle-verifier agreement 1.000, speed basis labelled.`
