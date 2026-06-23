# RouteMap Token Importance

Chris's instinct: group words into value-types. Function words like `a`, `an`, `the`, and `them` are usually cheap; content words like `island` and `artist` are richer. Small codes for common words are not the point by themselves. The disciplined version is a route score attached to each token:

1. Cheap static class + IDF prior gives the instant first guess.
2. Contextual checks rescue load-bearing tokens.
3. The route policy sends low-value tokens to `cheap` and keeps risky/content tokens.

The value is the route score, not an integer id. Low-value tokens route to a cheap path; content/load-bearing tokens are kept. The contextual check is what prevents discarding a load-bearing `the` or `not`.

## Public API

```python
from routemap_token import classify_token, run_benchmark, route_action, token_prior_score
```

## Leakage Guard

Contextual scoring does not accept gold answer or evidence spans. Inference-time signals are question overlap, entity flag, negation/modal status, position, citation boundary, quote boundary, and neighbors. Gold answer/evidence are used only in `bench.py` for `later_needed` labels and recall metrics.

## CLI

```powershell
$env:PYTHONPATH='src'
python -B -m routemap_token run --out %TEMP%\\routemap_token_bench
```

Outputs, when `--out` is supplied:

- `token_importance_traces.jsonl`
- `token_routeqa_card.md`
- `summary.json`
