# Full Extraction Soft-Entity Evaluation

| total rows | 72 |
| excluded rows | 0 |
| evaluated rows | 72 |
| entity matcher | soft_embedding |
| role accuracy | 0.306 |
| entity average soft Jaccard | 0.159 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.042 |
| relaxed_2 | 0.042 |
| relaxed_3 | 0.125 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| role+status+relation+entity_exact+entity_jaccard_lt_0.5 | 17 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 15 |
| entity_exact+entity_jaccard_lt_0.5 | 9 |
| role+status+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 6 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 3 |
| status+relation+entity_exact+entity_jaccard_lt_0.5 | 3 |
| answer+entity_exact+entity_jaccard_lt_0.5 | 3 |
| role+status+relation | 3 |
| entity_exact | 3 |
| role+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+relation+entity_exact | 2 |
| role+relation | 2 |
| role+status+relation+answer+entity_exact | 2 |
| status+entity_exact+entity_jaccard_lt_0.5 | 1 |
| role+status+relation+entity_exact | 1 |