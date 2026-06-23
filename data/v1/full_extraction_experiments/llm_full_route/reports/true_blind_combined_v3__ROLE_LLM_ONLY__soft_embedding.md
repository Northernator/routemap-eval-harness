# Full Extraction Soft-Entity Evaluation

| total rows | 72 |
| excluded rows | 0 |
| evaluated rows | 72 |
| entity matcher | soft_embedding |
| role accuracy | 0.556 |
| entity average soft Jaccard | 0.022 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.000 |
| relaxed_2 | 0.000 |
| relaxed_3 | 0.000 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| status+relation+entity_exact+entity_jaccard_lt_0.5 | 16 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 12 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 10 |
| entity_exact+entity_jaccard_lt_0.5 | 8 |
| role+status+relation+entity_exact+entity_jaccard_lt_0.5 | 8 |
| status+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 6 |
| role+entity_exact+entity_jaccard_lt_0.5 | 4 |
| role+answer+entity_exact+entity_jaccard_lt_0.5 | 3 |
| role+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+status+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+status+entity_exact+entity_jaccard_lt_0.5 | 1 |