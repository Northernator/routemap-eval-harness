# Full Extraction Soft-Entity Evaluation

| total rows | 72 |
| excluded rows | 0 |
| evaluated rows | 72 |
| entity matcher | soft_difflib |
| role accuracy | 0.556 |
| entity average soft Jaccard | 0.128 |
| strict full-row accuracy | 0.014 |
| relaxed_1 | 0.069 |
| relaxed_2 | 0.069 |
| relaxed_3 | 0.083 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact+entity_jaccard_lt_0.5 | 35 |
| role+entity_exact+entity_jaccard_lt_0.5 | 28 |
| entity_exact | 4 |
| role+entity_exact | 3 |
| role | 1 |