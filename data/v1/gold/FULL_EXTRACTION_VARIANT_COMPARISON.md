# Full Extraction Variant Comparison

| variant | role acc | entity exact | entity Jaccard | relation acc | answer relevance | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| original | 0.329 | 0.025 | 0.326 | 0.316 | 0.886 | 0.000 | 0.025 | 0.089 | 0.152 |
| boundary_role_only | 0.532 | 0.025 | 0.326 | 0.443 | 0.886 | 0.000 | 0.127 | 0.139 | 0.152 |
| ontology_only | 0.329 | 0.076 | 0.506 | 0.316 | 0.886 | 0.013 | 0.165 | 0.278 | 0.430 |
| combined_v3 | 0.532 | 0.076 | 0.506 | 0.443 | 0.848 | 0.051 | 0.253 | 0.354 | 0.443 |

## Interpretation

Boundary-role augmentation improves role and relation fields. Ontology-only improves entity overlap but leaves role errors untouched. Combined v3 tests whether those two gains interact in full-extraction scoring without tuning either component on the fresh adjudicated test.