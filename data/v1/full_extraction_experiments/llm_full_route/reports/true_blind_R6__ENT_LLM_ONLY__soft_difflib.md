# Full Extraction Soft-Entity Evaluation

| total rows | 72 |
| excluded rows | 0 |
| evaluated rows | 72 |
| entity matcher | soft_difflib |
| role accuracy | 0.306 |
| entity average soft Jaccard | 0.128 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.028 |
| relaxed_2 | 0.028 |
| relaxed_3 | 0.083 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| role+status+relation+entity_exact+entity_jaccard_lt_0.5 | 18 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 17 |
| entity_exact+entity_jaccard_lt_0.5 | 10 |
| role+status+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 6 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 3 |
| status+relation+entity_exact+entity_jaccard_lt_0.5 | 3 |
| answer+entity_exact+entity_jaccard_lt_0.5 | 3 |
| role+status+relation+entity_exact | 2 |
| role+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+status+relation+answer+entity_exact | 2 |
| entity_exact | 2 |
| status+entity_exact+entity_jaccard_lt_0.5 | 1 |
| role+status+relation | 1 |
| role+relation | 1 |
| role+relation+entity_exact | 1 |