# Full Extraction Soft-Entity Evaluation

| total rows | 80 |
| excluded rows | 0 |
| evaluated rows | 80 |
| entity matcher | soft_difflib |
| role accuracy | 0.988 |
| entity average soft Jaccard | 0.479 |
| strict full-row accuracy | 0.250 |
| relaxed_1 | 0.537 |
| relaxed_2 | 0.537 |
| relaxed_3 | 0.537 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact+entity_jaccard_lt_0.5 | 31 |
| entity_exact | 19 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 5 |
| relation+entity_exact | 3 |
| role+relation | 1 |
| relation | 1 |