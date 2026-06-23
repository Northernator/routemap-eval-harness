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
| role accuracy | 0.988 |
| operative status accuracy | 1.000 |
| relation accuracy | 0.875 |
| answer relevance accuracy | 1.000 |
| entity exact match | 0.013 |
| entity average Jaccard | 0.021 |
| entity average precision | 0.022 |
| entity average recall | 0.031 |
| entity average F1 | 0.025 |
| zero entity overlap rows | 77 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.025 |
| relaxed_2 | 0.025 |
| relaxed_3 | 0.025 |

## Top Failure Patterns

| failure pattern | rows |
|---|---:|
| entity_exact+entity_jaccard_lt_0.5 | 69 |
| relation+entity_exact+entity_jaccard_lt_0.5 | 8 |
| role+relation+entity_exact+entity_jaccard_lt_0.5 | 1 |
| relation | 1 |
| entity_exact | 1 |

## Interpretation

Combined v3 improves the role and entity lanes together, but strict full-row accuracy remains constrained by exact entity-set matching and downstream status/relevance/relation mismatches. Relaxed scores show more useful route signal than strict exact-match scoring.

## Remaining Bottlenecks

- Exact entity-set extraction remains brittle.
- Derived status and answer relevance still introduce errors for background and limitation rows.
- Relation accuracy follows role quality but still fails when fine role prediction fails.