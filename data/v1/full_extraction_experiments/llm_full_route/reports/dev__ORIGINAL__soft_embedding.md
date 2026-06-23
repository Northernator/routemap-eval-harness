# Full Extraction Soft-Entity Evaluation

| total rows | 80 |
| excluded rows | 0 |
| evaluated rows | 80 |
| entity matcher | soft_embedding |
| role accuracy | 0.988 |
| entity average soft Jaccard | 0.714 |
| strict full-row accuracy | 0.475 |
| relaxed_1 | 0.838 |
| relaxed_2 | 0.838 |
| relaxed_3 | 0.838 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact | 22 |
| entity_exact+entity_jaccard_lt_0.5 | 10 |
| relation+entity_exact | 6 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+relation | 1 |
| relation | 1 |