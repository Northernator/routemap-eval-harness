# Full Extraction Soft-Entity Evaluation

| total rows | 80 |
| excluded rows | 0 |
| evaluated rows | 80 |
| entity matcher | soft_embedding |
| role accuracy | 0.825 |
| entity average soft Jaccard | 0.444 |
| strict full-row accuracy | 0.250 |
| relaxed_1 | 0.438 |
| relaxed_2 | 0.500 |
| relaxed_3 | 0.512 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact+entity_jaccard_lt_0.5 | 31 |
| entity_exact | 15 |
| role+entity_exact+entity_jaccard_lt_0.5 | 7 |
| role+entity_exact | 6 |
| role | 1 |