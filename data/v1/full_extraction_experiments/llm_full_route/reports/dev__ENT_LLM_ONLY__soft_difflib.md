# Full Extraction Soft-Entity Evaluation

| total rows | 80 |
| excluded rows | 0 |
| evaluated rows | 80 |
| entity matcher | soft_difflib |
| role accuracy | 0.988 |
| entity average soft Jaccard | 0.451 |
| strict full-row accuracy | 0.237 |
| relaxed_1 | 0.512 |
| relaxed_2 | 0.512 |
| relaxed_3 | 0.512 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact+entity_jaccard_lt_0.5 | 33 |
| entity_exact | 18 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 5 |
| relation+entity_exact | 3 |
| role+relation | 1 |
| relation | 1 |