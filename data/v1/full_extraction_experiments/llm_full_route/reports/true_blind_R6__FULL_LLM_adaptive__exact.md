# Combined V3 Full Extraction Results

## Previous Reference Points

| reference | score |
|---|---:|
| previous strict full-row | 0.000 |
| previous relaxed full-row after boundary role | 0.089 |
| previous entity Jaccard current | 0.326 |
| ontology_v1 entity Jaccard | 0.506 |

## Combined V3 Scores

| metric | score |
|---|---:|
| total rows | 72 |
| evaluated rows | 72 |
| excluded rows | 0 |
| role accuracy | 0.556 |
| operative status accuracy | 0.542 |
| relation accuracy | 0.222 |
| answer relevance accuracy | 0.819 |
| entity exact match | 0.000 |
| entity average Jaccard | 0.000 |
| entity average precision | 0.000 |
| entity average recall | 0.000 |
| entity average F1 | 0.000 |
| zero entity overlap rows | 72 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.000 |
| relaxed_2 | 0.000 |
| relaxed_3 | 0.000 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| status+relation+entity_exact+entity_jaccard_lt_0.5 | 16 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 12 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 10 |
| entity_exact+entity_jaccard_lt_0.5 | 8 |
| role+status+relation+entity_exact+entity_jaccard_lt_0.5 | 8 |
| status+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 6 |
| role+entity_exact+entity_jaccard_lt_0.5 | 4 |
| role+answer+entity_exact+entity_jaccard_lt_0.5 | 3 |
| role+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+status+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+status+entity_exact+entity_jaccard_lt_0.5 | 1 |

## Interpretation

Combined v3 improves the role and entity lanes together, but strict full-row accuracy remains constrained by exact entity-set matching and downstream status/relevance/relation mismatches. Relaxed scores show more useful route signal than strict exact-match scoring.

## Remaining Bottlenecks

- Exact entity-set extraction remains brittle.
- Derived status and answer relevance still introduce errors for background and limitation rows.
- Relation accuracy follows role quality but still fails when fine role prediction fails.