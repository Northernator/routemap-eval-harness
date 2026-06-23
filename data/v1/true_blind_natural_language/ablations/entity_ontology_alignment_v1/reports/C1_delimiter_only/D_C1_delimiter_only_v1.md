# Entity Alignment Ablation Evaluation

- ontology: `v1`
- status: ABLATION ONLY; not locked true-blind scoring.

## Metrics

| metric | value |
|---|---:|
| evaluated_rows | 72 |
| missing_invalid_rows | 0 |
| role | 0.236111 |
| coarse_5 | 0.236111 |
| coarse_4 | 0.236111 |
| coarse_3 | 0.305556 |
| entity_jaccard | 0.011806 |
| entity_exact | 0.000000 |
| status | 0.361111 |
| relation | 0.222222 |
| answer | 0.819444 |
| strict | 0.000000 |
| relaxed_1 | 0.000000 |
| relaxed_2 | 0.000000 |
| relaxed_3 | 0.000000 |

## Failure Patterns

| pattern | rows |
|---|---:|
| role+entity+status+relation | 36 |
| role+entity+relation | 11 |
| entity | 9 |
| role+entity+status+relation+answer | 6 |
| entity+answer | 4 |
| entity+status | 3 |
| role+entity+relation+answer | 2 |
| entity+status+relation+answer | 1 |
