# Full Extraction Soft-Entity Evaluation

| total rows | 80 |
| excluded rows | 0 |
| evaluated rows | 80 |
| entity matcher | soft_embedding |
| role accuracy | 0.988 |
| entity average soft Jaccard | 0.087 |
| strict full-row accuracy | 0.013 |
| relaxed_1 | 0.087 |
| relaxed_2 | 0.087 |
| relaxed_3 | 0.087 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact+entity_jaccard_lt_0.5 | 64 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 8 |
| entity_exact | 5 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 1 |
| relation | 1 |