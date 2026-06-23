# Full Extraction Soft-Entity Evaluation

| total rows | 80 |
| excluded rows | 0 |
| evaluated rows | 80 |
| entity matcher | soft_difflib |
| role accuracy | 0.825 |
| entity average soft Jaccard | 0.712 |
| strict full-row accuracy | 0.425 |
| relaxed_1 | 0.700 |
| relaxed_2 | 0.787 |
| relaxed_3 | 0.812 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact | 15 |
| entity_exact+entity_jaccard_lt_0.5 | 8 |
| role+entity_exact | 7 |
| relation+entity_exact | 5 |
| role | 4 |
| relation | 2 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+relation+entity_exact | 1 |