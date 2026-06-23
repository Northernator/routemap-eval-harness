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
| evaluated rows | 80 |
| excluded rows | 0 |
| role accuracy | 0.825 |
| operative status accuracy | 1.000 |
| relation accuracy | 0.875 |
| answer relevance accuracy | 1.000 |
| entity exact match | 0.512 |
| entity average Jaccard | 0.720 |
| entity average precision | 0.778 |
| entity average recall | 0.830 |
| entity average F1 | 0.782 |
| zero entity overlap rows | 7 |
| strict full-row accuracy | 0.425 |
| relaxed_1 | 0.700 |
| relaxed_2 | 0.787 |
| relaxed_3 | 0.812 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact | 15 |
| entity_exact+entity_jaccard_lt_0.5 | 8 |
| role+entity_exact | 6 |
| relation+entity_exact | 5 |
| role | 5 |
| relation | 2 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+entity_exact+entity_jaccard_lt_0.5 | 2 |
| role+relation+entity_exact | 1 |

## Interpretation

Combined v3 improves the role and entity lanes together, but strict full-row accuracy remains constrained by exact entity-set matching and downstream status/relevance/relation mismatches. Relaxed scores show more useful route signal than strict exact-match scoring.

## Remaining Bottlenecks

- Exact entity-set extraction remains brittle.
- Derived status and answer relevance still introduce errors for background and limitation rows.
- Relation accuracy follows role quality but still fails when fine role prediction fails.