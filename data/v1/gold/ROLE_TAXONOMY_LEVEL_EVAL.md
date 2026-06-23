# Role Taxonomy Level Evaluation

## Model x Taxonomy Accuracy

| model | fine_8 | coarse_5 | coarse_4 | coarse_3 |
|---|---|---|---|---|
| pred_word_unigram_nb | 0.443 | 0.557 | 0.620 | 0.810 |
| pred_word_unigram_bigram_nb | 0.443 | 0.557 | 0.633 | 0.810 |
| pred_char_3_5gram_nb | 0.405 | 0.481 | 0.557 | 0.785 |
| pred_centroid | 0.456 | 0.582 | 0.620 | 0.797 |

## Best Model Per Taxonomy

| taxonomy | best_model | accuracy |
|---|---|---:|
| fine_8 | pred_centroid | 0.456 |
| coarse_5 | pred_centroid | 0.582 |
| coarse_4 | pred_word_unigram_bigram_nb | 0.633 |
| coarse_3 | pred_word_unigram_nb | 0.810 |

## Best Taxonomy Per Model

| model | best_taxonomy | accuracy |
|---|---|---:|
| pred_word_unigram_nb | coarse_3 | 0.810 |
| pred_word_unigram_bigram_nb | coarse_3 | 0.810 |
| pred_char_3_5gram_nb | coarse_3 | 0.785 |
| pred_centroid | coarse_3 | 0.797 |

## fine_8: `pred_centroid`

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

## coarse_5: `pred_centroid`

| gold\pred | ACTION | ASSERTION | CAVEAT | CONTEXT | INSTANCE |
|---|---|---|---|---|---|
| ACTION | 9 | 8 | 0 | 1 | 1 |
| ASSERTION | 4 | 22 | 1 | 2 | 1 |
| CAVEAT | 2 | 1 | 6 | 0 | 1 |
| CONTEXT | 1 | 4 | 1 | 2 | 2 |
| INSTANCE | 2 | 1 | 0 | 0 | 7 |

## coarse_4: `pred_word_unigram_bigram_nb`

| gold\pred | ACTION | CAVEAT | CONTENT | CONTEXT |
|---|---|---|---|---|
| ACTION | 21 | 0 | 7 | 1 |
| CAVEAT | 3 | 6 | 1 | 0 |
| CONTENT | 7 | 1 | 21 | 1 |
| CONTEXT | 3 | 2 | 3 | 2 |

## coarse_3: `pred_word_unigram_nb`

| gold\pred | CAVEAT | CONTEXT | SUBSTANTIVE |
|---|---|---|---|
| CAVEAT | 6 | 0 | 4 |
| CONTEXT | 2 | 4 | 4 |
| SUBSTANTIVE | 2 | 3 | 54 |

## Interpretation

Fine and coarse scores should both be reported. Coarse taxonomy gains indicate that models have route-function signal even when they miss fine-grained role boundaries.