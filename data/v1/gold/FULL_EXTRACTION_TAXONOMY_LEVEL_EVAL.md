# Full Extraction Taxonomy Level Evaluation

| taxonomy | role_accuracy | relation_accuracy | entity_exact | entity_jaccard | strict | relaxed_strict |
|---|---:|---:|---:|---:|---:|---:|
| fine_8 | 0.329 | 0.316 | 0.013 | 0.283 | 0.000 | 0.025 |
| coarse_5 | 0.506 | 0.316 | 0.013 | 0.283 | 0.000 | 0.076 |
| coarse_4 | 0.506 | 0.316 | 0.013 | 0.283 | 0.000 | 0.076 |
| coarse_3 | 0.797 | 0.316 | 0.013 | 0.283 | 0.000 | 0.127 |

## Interpretation

Strict full extraction remains hard because entity exact match and downstream relation/status fields still constrain success. Relaxed strict shows whether mapped role plus answer relevance plus partial entity overlap is improving under coarser taxonomies.