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
| total rows | 80 |
| evaluated rows | 79 |
| excluded rows | 1 |
| role accuracy | 0.532 |
| operative status accuracy | 0.595 |
| relation accuracy | 0.443 |
| answer relevance accuracy | 0.848 |
| entity exact match | 0.076 |
| entity average Jaccard | 0.506 |
| entity average precision | 0.759 |
| entity average recall | 0.589 |
| entity average F1 | 0.634 |
| zero entity overlap rows | 5 |
| strict full-row accuracy | 0.051 |
| relaxed_1 | 0.253 |
| relaxed_2 | 0.354 |
| relaxed_3 | 0.443 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| role+status+relation+entity_exact | 17 |
| entity_exact+entity_jaccard_lt_0.5 | 17 |
| entity_exact | 10 |
| role+status+relation+entity_exact+entity_jaccard_lt_0.5 | 8 |
| relation+entity_exact | 6 |
| role+status+relation+answer+entity_exact | 5 |
| answer+entity_exact | 3 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 2 |
| answer | 1 |
| role+relation+answer+entity_exact | 1 |
| role+status+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 1 |
| role+relation+entity_exact | 1 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 1 |
| role+status+relation | 1 |
| role+relation+answer+entity_exact+entity_jaccard_lt_0.5 | 1 |

## Interpretation

Combined v3 improves the role and entity lanes together, but strict full-row accuracy remains constrained by exact entity-set matching and downstream status/relevance/relation mismatches. Relaxed scores show more useful route signal than strict exact-match scoring.

## Remaining Bottlenecks

- Exact entity-set extraction remains brittle.
- Derived status and answer relevance still introduce errors for background and limitation rows.
- Relation accuracy follows role quality but still fails when fine role prediction fails.