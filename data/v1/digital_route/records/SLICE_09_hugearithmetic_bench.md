# Phase 3 Slice 9 - HugeArithmeticRouteBench

Date: 2026-06-23

## Purpose

Add a reproducible model-agnostic arithmetic route benchmark that measures route answering, verifier catch rate, blind spots, coverage, and compute-saved reporting without modifying the Digital Route engine.

## Files created

- `src/routemap_bench/__init__.py`
- `src/routemap_bench/tasks.py`
- `src/routemap_bench/solvers.py`
- `src/routemap_bench/route.py`
- `src/routemap_bench/metrics.py`
- `src/routemap_bench/run_bench.py`
- `src/routemap_bench/__main__.py`
- `src/routemap_bench/README.md`
- `rb_test_bench.py`
- `data/v1/digital_route/slice_09_hugearith/random/tasks.jsonl`
- `data/v1/digital_route/slice_09_hugearith/random/results.csv`
- `data/v1/digital_route/slice_09_hugearith/random/summary.json`
- `data/v1/digital_route/slice_09_hugearith/random/benchmark_card.md`
- `data/v1/digital_route/slice_09_hugearith/off_by_M/tasks.jsonl`
- `data/v1/digital_route/slice_09_hugearith/off_by_M/results.csv`
- `data/v1/digital_route/slice_09_hugearith/off_by_M/summary.json`
- `data/v1/digital_route/slice_09_hugearith/off_by_M/benchmark_card.md`
- `data/v1/digital_route/records/SLICE_09_hugearithmetic_bench.md`

## Commands run

- `$env:PYTHONPATH='src'; python -m py_compile src/routemap_bench/__init__.py src/routemap_bench/tasks.py src/routemap_bench/solvers.py src/routemap_bench/route.py src/routemap_bench/metrics.py src/routemap_bench/run_bench.py src/routemap_bench/__main__.py`
- `$env:PYTHONPATH='src'; python -m pytest rb_test_bench.py -q`
- `$env:PYTHONPATH='src'; python -m routemap_bench run --solver noisy --error random --p 0.5 --n 200 --seed 7 --out data/v1/digital_route/slice_09_hugearith/random`
- `$env:PYTHONPATH='src'; python -m routemap_bench run --solver noisy --error off_by_M --p 0.5 --n 200 --seed 7 --out data/v1/digital_route/slice_09_hugearith/off_by_M`

## Families

- `digital_root`
- `mod_m`
- `last_k_digits`
- `divisibility`
- `impossibility`
- `linear_recurrence_residue`
- `fibonacci_state`
- `pascal_row_entry`

## Ground-Truth Independence Guard

Ground truth is computed in `routemap_bench.tasks` using Python stdlib algorithms independent of `routemap_digital`: 3-arg `pow`, `math.factorial`/modular factorial, separate fast-doubling Fibonacci, separate matrix-power recurrence, and Lucas' theorem for Pascal row entries.

## Honesty Caveats

`impossibility` and `pascal_row_entry` are counted outside the route-answerable subset. Route answers are residue/predicate answers, not claims of full integer reconstruction. Off-by-modulus claims are expected blind spots and return `NOT_RULED_OUT`, not a false "correct".

## Offline Random-Error Metrics

| Metric | Value |
| --- | ---: |
| raw_solver_accuracy | 0.530 |
| route_engine_accuracy | 1.000 |
| verifier_catch_rate | 1.000 |
| false_rejection_rate | 0.000 |
| route_decidable_coverage | 0.750 |
| blind_spot_rate | 0.000 |
| compute_saved | 3.690x |
| full_expansion_impossible_cases | 73 |
| verifier_minimum_bar | PASS |
| verifier_strong_bar | PASS |
| speed_minimum_bar | PASS |
| speed_strong_bar | PASS |

## Offline Off-by-M Metrics

| Metric | Value |
| --- | ---: |
| raw_solver_accuracy | 0.550 |
| route_engine_accuracy | 1.000 |
| verifier_catch_rate | 1.000 |
| false_rejection_rate | 0.000 |
| route_decidable_coverage | 0.750 |
| blind_spot_rate | 0.000 |
| blind_spot_n | 55 |
| compute_saved | 3.692x |
| full_expansion_impossible_cases | 73 |
| verifier_minimum_bar | PASS |
| verifier_strong_bar | PASS |
| speed_minimum_bar | PASS |
| speed_strong_bar | PASS |

The off-by-M run has `blind_spot_rate=0.000`, meaning none of the exact modulus-multiple wrong integer claims were caught. These remain `NOT_RULED_OUT` cases, not false correctness claims.

## Index Note

`PHASE3_INDEX.md` was intentionally left unchanged to preserve the new-files-only constraint. Suggested index row:

`- 2026-06-23 - Slice 09: HugeArithmeticRouteBench model-agnostic arithmetic route benchmark; offline random/off_by_M runs recorded.`
