# Role Model Baselines: Fresh Adjudicated Test

## Data

| source | rows |
|---|---:|
| seed_train | 99 |
| heldout_v1_dev | 80 |
| fresh_v2_adjudicated_test | 79 |

## Accuracy

| model | accuracy |
|---|---:|
| word_unigram_nb | 0.443 |
| word_unigram_bigram_nb | 0.443 |
| char_3_5gram_nb | 0.405 |
| simple_centroid_tfidf_like | 0.456 |

Best model: `simple_centroid_tfidf_like` at 0.456.

## Per-Role F1

| role | word_unigram_nb | word_unigram_bigram_nb | char_3_5gram_nb | simple_centroid_tfidf_like |
|---|---:|---:|---:|---:|
| BACKGROUND | 0.471 | 0.286 | 0.308 | 0.267 |
| CLAIM | 0.250 | 0.261 | 0.348 | 0.320 |
| DEFINE | 0.353 | 0.522 | 0.706 | 0.560 |
| METHOD | 0.320 | 0.261 | 0.286 | 0.348 |
| RESULT | 0.429 | 0.500 | 0.267 | 0.250 |
| LIMITATION | 0.600 | 0.632 | 0.556 | 0.667 |
| NEXT_STEP | 0.667 | 0.588 | 0.500 | 0.571 |
| EXAMPLE | 0.538 | 0.522 | 0.381 | 0.636 |

## Comparison Against Previous Baselines

| baseline | accuracy |
|---|---:|
| Rule v2 | 0.329 |
| Naive Bayes | 0.430 |
| Hybrid | 0.418 |
| Best new text baseline | 0.456 |

## Interpretation

The standard-library text baselines remain small-data baselines. They are trained only on the model-ready train/dev file and evaluated once on the locked fresh adjudicated test file. The result should guide the next modelling phase, not replace a larger validation protocol.

Next recommendation: use the train/dev file for cross-validation and feature experiments, keep the fresh adjudicated test locked, and evaluate stronger learned role models only after development choices are fixed.