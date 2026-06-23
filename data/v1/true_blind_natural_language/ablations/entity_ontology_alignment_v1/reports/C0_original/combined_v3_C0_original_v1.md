# Entity Alignment Ablation Evaluation

- ontology: `v1`
- status: ABLATION ONLY; not locked true-blind scoring.

## Metrics

| metric | value |
|---|---:|
| evaluated_rows | 72 |
| missing_invalid_rows | 0 |
| role | 0.305556 |
| coarse_5 | 0.347222 |
| coarse_4 | 0.361111 |
| coarse_3 | 0.555556 |
| entity_jaccard | 0.000000 |
| entity_exact | 0.000000 |
| status | 0.541667 |
| relation | 0.222222 |
| answer | 0.819444 |
| strict | 0.000000 |
| relaxed_1 | 0.000000 |
| relaxed_2 | 0.000000 |
| relaxed_3 | 0.000000 |

## Failure Patterns

| pattern | rows |
|---|---:|
| role+entity+status+relation | 21 |
| role+entity+relation | 19 |
| entity | 12 |
| role+entity+status+relation+answer | 8 |
| entity+relation | 3 |
| entity+status+relation | 3 |
| entity+answer | 3 |
| role+entity+relation+answer | 2 |
| entity+status | 1 |
