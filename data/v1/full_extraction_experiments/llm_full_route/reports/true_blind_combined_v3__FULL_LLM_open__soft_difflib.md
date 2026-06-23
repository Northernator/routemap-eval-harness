# Full Extraction Soft-Entity Evaluation

| total rows | 72 |
| excluded rows | 0 |
| evaluated rows | 72 |
| entity matcher | soft_difflib |
| role accuracy | 0.556 |
| entity average soft Jaccard | 0.151 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.083 |
| relaxed_2 | 0.111 |
| relaxed_3 | 0.111 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| status+relation+entity_exact+entity_jaccard_lt_0.5 | 13 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 10 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 8 |
| entity_exact+entity_jaccard_lt_0.5 | 7 |
| role+status+relation+entity_exact+entity_jaccard_lt_0.5 | 7 |
| status+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 5 |
| role+answer+entity_exact+entity_jaccard_lt_0.5 | 3 |
| role+entity_exact+entity_jaccard_lt_0.5 | 2 |
| status+relation+entity_exact | 2 |
| role+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+entity_exact | 2 |
| relation+entity_exact | 2 |
| role+status+entity_exact+entity_jaccard_lt_0.5 | 1 |
| role+relation+entity_exact | 1 |
| status+relation | 1 |