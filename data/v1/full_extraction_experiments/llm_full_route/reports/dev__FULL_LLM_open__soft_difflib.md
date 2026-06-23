# Full Extraction Soft-Entity Evaluation

| total rows | 80 |
| excluded rows | 0 |
| evaluated rows | 80 |
| entity matcher | soft_difflib |
| role accuracy | 0.825 |
| entity average soft Jaccard | 0.064 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.037 |
| relaxed_2 | 0.050 |
| relaxed_3 | 0.062 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact+entity_jaccard_lt_0.5 | 54 |
| role+entity_exact+entity_jaccard_lt_0.5 | 11 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 9 |
| entity_exact | 3 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 1 |
| role | 1 |
| role+entity_exact | 1 |