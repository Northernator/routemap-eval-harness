# HugeArithmeticRouteBench

HugeArithmeticRouteBench is a model-agnostic benchmark for Digital Route arithmetic. It measures where the route engine can answer residue questions directly and where the verifier can rule out inconsistent claims.

## Methodology Guard

Ground truth is computed independently in `routemap_bench.tasks` using Python stdlib algorithms:

- `pow(base, exponent, modulus)` for modular powers
- `math.factorial` or modular factorial with trailing-zero shortcut for last digits
- separate fast-doubling Fibonacci
- separate matrix-power linear recurrence
- Lucas' theorem for Pascal row entries

The benchmark does not use `routemap_digital` as ground truth.

## Offline Run

```powershell
$env:PYTHONPATH='src'
python -m routemap_bench run --solver noisy --error random --p 0.5 --n 200 --seed 7 --out data/v1/digital_route/slice_09_hugearith/random
python -m routemap_bench run --solver noisy --error off_by_M --p 0.5 --n 200 --seed 7 --out data/v1/digital_route/slice_09_hugearith/off_by_M
```

Outputs:

- `tasks.jsonl`: frozen tasks and independent GT
- `results.csv`: per-task route/verifier result
- `summary.json`: machine-readable metrics
- `benchmark_card.md`: metrics table, bars, coverage, caveats

`--solver ollama` is optional and local-only; it is never required for the default run.
