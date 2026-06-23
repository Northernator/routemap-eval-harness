# Grouped Role Taxonomy Results

## Accuracy Summary

| taxonomy | best_model | best_accuracy | pred_word_unigram_nb | pred_word_unigram_bigram_nb | pred_char_3_5gram_nb | pred_centroid |
|---|---|---:|---:|---:|---:|---:|
| A_8_role_original | pred_centroid | 0.456 | 0.443 | 0.443 | 0.405 | 0.456 |
| B_5_role_compressed | pred_centroid | 0.582 | 0.557 | 0.557 | 0.481 | 0.582 |
| C_4_role_compressed | pred_word_unigram_bigram_nb | 0.633 | 0.620 | 0.633 | 0.557 | 0.620 |
| D_3_role_compressed | pred_word_unigram_nb | 0.810 | 0.810 | 0.810 | 0.785 | 0.797 |

## A_8_role_original: Best Model `pred_centroid`

| group | precision | recall | F1 | support |
|---|---:|---:|---:|---:|
| BACKGROUND | 0.400 | 0.200 | 0.267 | 10 |
| CLAIM | 0.267 | 0.400 | 0.320 | 10 |
| DEFINE | 0.467 | 0.700 | 0.560 | 10 |
| EXAMPLE | 0.583 | 0.700 | 0.636 | 10 |
| LIMITATION | 0.750 | 0.600 | 0.667 | 10 |
| METHOD | 0.308 | 0.400 | 0.348 | 10 |
| NEXT_STEP | 0.800 | 0.444 | 0.571 | 9 |
| RESULT | 0.333 | 0.200 | 0.250 | 10 |

Confusion matrix:

| gold\pred | BACKGROUND | CLAIM | DEFINE | EXAMPLE | LIMITATION | METHOD | NEXT_STEP | RESULT |
|---|---|---|---|---|---|---|---|---|
| BACKGROUND | 2 | 2 | 0 | 2 | 1 | 0 | 1 | 2 |
| CLAIM | 1 | 4 | 3 | 0 | 1 | 1 | 0 | 0 |
| DEFINE | 0 | 2 | 7 | 0 | 0 | 1 | 0 | 0 |
| EXAMPLE | 0 | 0 | 1 | 7 | 0 | 2 | 0 | 0 |
| LIMITATION | 0 | 1 | 0 | 1 | 6 | 2 | 0 | 0 |
| METHOD | 0 | 2 | 2 | 1 | 0 | 4 | 0 | 1 |
| NEXT_STEP | 1 | 1 | 1 | 0 | 0 | 1 | 4 | 1 |
| RESULT | 1 | 3 | 1 | 1 | 0 | 2 | 0 | 2 |

## B_5_role_compressed: Best Model `pred_centroid`

| group | precision | recall | F1 | support |
|---|---:|---:|---:|---:|
| ACTION | 0.500 | 0.474 | 0.486 | 19 |
| ASSERTION | 0.611 | 0.733 | 0.667 | 30 |
| CAVEAT | 0.750 | 0.600 | 0.667 | 10 |
| CONTEXT | 0.400 | 0.200 | 0.267 | 10 |
| INSTANCE | 0.583 | 0.700 | 0.636 | 10 |

Confusion matrix:

| gold\pred | ACTION | ASSERTION | CAVEAT | CONTEXT | INSTANCE |
|---|---|---|---|---|---|
| ACTION | 9 | 8 | 0 | 1 | 1 |
| ASSERTION | 4 | 22 | 1 | 2 | 1 |
| CAVEAT | 2 | 1 | 6 | 0 | 1 |
| CONTEXT | 1 | 4 | 1 | 2 | 2 |
| INSTANCE | 2 | 1 | 0 | 0 | 7 |

## C_4_role_compressed: Best Model `pred_word_unigram_bigram_nb`

| group | precision | recall | F1 | support |
|---|---:|---:|---:|---:|
| ACTION | 0.618 | 0.724 | 0.667 | 29 |
| CAVEAT | 0.667 | 0.600 | 0.632 | 10 |
| CONTENT | 0.656 | 0.700 | 0.677 | 30 |
| CONTEXT | 0.500 | 0.200 | 0.286 | 10 |

Confusion matrix:

| gold\pred | ACTION | CAVEAT | CONTENT | CONTEXT |
|---|---|---|---|---|
| ACTION | 21 | 0 | 7 | 1 |
| CAVEAT | 3 | 6 | 1 | 0 |
| CONTENT | 7 | 1 | 21 | 1 |
| CONTEXT | 3 | 2 | 3 | 2 |

## D_3_role_compressed: Best Model `pred_word_unigram_nb`

| group | precision | recall | F1 | support |
|---|---:|---:|---:|---:|
| CAVEAT | 0.600 | 0.600 | 0.600 | 10 |
| CONTEXT | 0.571 | 0.400 | 0.471 | 10 |
| SUBSTANTIVE | 0.871 | 0.915 | 0.893 | 59 |

Confusion matrix:

| gold\pred | CAVEAT | CONTEXT | SUBSTANTIVE |
|---|---|---|---|
| CAVEAT | 6 | 0 | 4 |
| CONTEXT | 2 | 4 | 4 |
| SUBSTANTIVE | 2 | 3 | 54 |

## Interpretation

If compressed taxonomies score much higher than the 8-role original, the current taxonomy is too fine for the available data/features. If compressed taxonomies still perform weakly, the representation or model family is also weak.

These grouped results are diagnostic only. They do not replace the 8-role benchmark.