# Full Extraction Boundary-Augmented Role Results

## Transfer Summary

| metric | original | boundary_augmented_role | delta |
|---|---:|---:|---:|
| role_accuracy | 0.329 | 0.532 | +0.203 |
| relation_accuracy | 0.316 | 0.443 | +0.127 |
| strict_full_row_accuracy | 0.000 | 0.000 | +0.000 |
| relaxed_full_row_accuracy | 0.025 | 0.089 | +0.063 |
| entity_exact_match | 0.013 | 0.013 | +0.000 |
| entity_average_jaccard | 0.283 | 0.283 | +0.000 |

Best boundary-augmented role model: `base_plus_boundary_train` / `centroid` at 0.532.

Entity predictions are unchanged in this comparison.

## Remaining Boundary-Augmented Role Confusions

| gold | pred | count |
|---|---|---:|
| DEFINE | CLAIM | 3 |
| RESULT | CLAIM | 3 |
| METHOD | EXAMPLE | 2 |
| METHOD | CLAIM | 2 |
| RESULT | METHOD | 2 |
| LIMITATION | EXAMPLE | 2 |
| LIMITATION | METHOD | 2 |
| NEXT_STEP | EXAMPLE | 2 |
| EXAMPLE | METHOD | 2 |
| BACKGROUND | RESULT | 1 |