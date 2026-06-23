# RouteMap v1 Benchmark Card

## What Has Been Built

- Corpus ingestion and route-oriented annotation rows.
- Clean CSV datasets for role and full extraction experiments.
- Deterministic role classifiers and baseline full extractors.
- No-leak tests separating heading-aware performance from text-only generalisation.
- Held-out v1 and fresh held-out v2 tests.
- Manual adjudication workflow for the fresh held-out v2 role set.
- Full extraction evaluator with role, relation, operative status, answer relevance, entity, and strict-row metrics.
- Grouped taxonomy diagnostics for fine and coarse route-function evaluation.

## Best Honest Current Scores

| metric | score |
|---|---:|
| Best fine 8-role score | 0.456 |
| Best 5-role score | 0.582 |
| Best 4-role score | 0.633 |
| Best 3-role score | 0.810 |
| Adjudicated full strict score | 0.000 |
| Entity average Jaccard | 0.283 |

## Main Conclusion

The pipeline works: RouteMap can create datasets, run extractors, evaluate held-out generalisation, adjudicate labels, and report fine/coarse benchmark scores.

Exact 8-role extraction is not solved. Coarse route grouping shows meaningful signal, especially under 3-role and 4-role taxonomies, but fine-grained role boundaries remain hard. Entity extraction remains weak and is a separate bottleneck for strict full-row extraction.

## What Should Not Be Claimed

- Do not claim robust route understanding yet.
- Do not cite seed 1.000 scores as generalisation evidence.
- Do not treat tuned development-set scores as final evidence.
- Do not tune on the locked fresh adjudicated test set.

## Next Recommended Work

- Collect boundary-pair data for the hardest fine-role distinctions.
- Evaluate stronger classifiers or LLM route extraction using train/dev data only for iteration.
- Build a separate entity extraction benchmark and improve entity modelling independently.
- Keep fine and coarse scores in all reports so progress is visible at both exact-role and route-function levels.
