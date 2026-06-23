# Full Extraction Soft-Entity Evaluation

| total rows | 72 |
| excluded rows | 0 |
| evaluated rows | 72 |
| entity matcher | soft_difflib |
| role accuracy | 0.306 |
| entity average soft Jaccard | 0.021 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.000 |
| relaxed_2 | 0.000 |
| relaxed_3 | 0.000 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| role+status+relation+entity_exact+entity_jaccard_lt_0.5 | 21 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 19 |
| entity_exact+entity_jaccard_lt_0.5 | 12 |
| role+status+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 8 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 3 |
| status+relation+entity_exact+entity_jaccard_lt_0.5 | 3 |
| answer+entity_exact+entity_jaccard_lt_0.5 | 3 |
| role+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 2 |
| status+entity_exact+entity_jaccard_lt_0.5 | 1 |