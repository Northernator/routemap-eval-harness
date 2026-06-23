# Full Extraction Soft-Entity Evaluation

| total rows | 80 |
| excluded rows | 0 |
| evaluated rows | 80 |
| entity matcher | soft_embedding |
| role accuracy | 0.825 |
| entity average soft Jaccard | 0.444 |
| strict full-row accuracy | 0.225 |
| relaxed_1 | 0.438 |
| relaxed_2 | 0.500 |
| relaxed_3 | 0.512 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact+entity_jaccard_lt_0.5 | 26 |
| entity_exact | 13 |
| role+entity_exact+entity_jaccard_lt_0.5 | 7 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 5 |
| role+entity_exact | 5 |
| relation | 2 |
| relation+entity_exact | 2 |
| role+relation+entity_exact | 1 |
| role | 1 |