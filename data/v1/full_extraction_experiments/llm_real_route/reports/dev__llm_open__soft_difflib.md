# Full Extraction Soft-Entity Evaluation

| total rows | 80 |
| excluded rows | 0 |
| evaluated rows | 80 |
| entity matcher | soft_difflib |
| role accuracy | 0.988 |
| entity average soft Jaccard | 0.064 |
| strict full-row accuracy | 0.013 |
| relaxed_1 | 0.062 |
| relaxed_2 | 0.062 |
| relaxed_3 | 0.062 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact+entity_jaccard_lt_0.5 | 65 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 9 |
| entity_exact | 4 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 1 |