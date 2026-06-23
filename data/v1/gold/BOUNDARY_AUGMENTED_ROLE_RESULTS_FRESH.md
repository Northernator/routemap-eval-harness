# Boundary-Augmented Role Results on Fresh Adjudicated Test

## Accuracy By Setting And Model

| setting | model | accuracy | delta_vs_previous_0.456 |
|---|---|---:|---:|
| base_only | word_unigram_nb | 0.443 | -0.013 |
| base_only | word_unigram_bigram_nb | 0.443 | -0.013 |
| base_only | char_3_5gram_nb | 0.405 | -0.051 |
| base_only | centroid | 0.456 | -0.000 |
| base_plus_boundary_train | word_unigram_nb | 0.456 | -0.000 |
| base_plus_boundary_train | word_unigram_bigram_nb | 0.456 | -0.000 |
| base_plus_boundary_train | char_3_5gram_nb | 0.418 | -0.038 |
| base_plus_boundary_train | centroid | 0.532 | +0.076 |
| base_plus_boundary_train_dev | word_unigram_nb | 0.468 | +0.012 |
| base_plus_boundary_train_dev | word_unigram_bigram_nb | 0.430 | -0.026 |
| base_plus_boundary_train_dev | char_3_5gram_nb | 0.418 | -0.038 |
| base_plus_boundary_train_dev | centroid | 0.519 | +0.063 |

Best model overall: `base_plus_boundary_train` / `centroid` at 0.532.

## Per-Role Metrics For Best Model

| role | precision | recall | F1 | support |
|---|---:|---:|---:|---:|
| BACKGROUND | 0.600 | 0.600 | 0.600 | 10 |
| CLAIM | 0.357 | 0.500 | 0.417 | 10 |
| DEFINE | 0.667 | 0.600 | 0.632 | 10 |
| METHOD | 0.357 | 0.500 | 0.417 | 10 |
| RESULT | 0.625 | 0.500 | 0.556 | 10 |
| LIMITATION | 0.667 | 0.400 | 0.500 | 10 |
| NEXT_STEP | 1.000 | 0.444 | 0.615 | 9 |
| EXAMPLE | 0.500 | 0.700 | 0.583 | 10 |

## Confusion Matrix For Best Model

| gold\pred | BACKGROUND | CLAIM | DEFINE | METHOD | RESULT | LIMITATION | NEXT_STEP | EXAMPLE |
|---|---|---|---|---|---|---|---|---|
| BACKGROUND | 6 | 1 | 0 | 1 | 1 | 1 | 0 | 0 |
| CLAIM | 1 | 5 | 1 | 1 | 0 | 1 | 0 | 1 |
| DEFINE | 0 | 3 | 6 | 1 | 0 | 0 | 0 | 0 |
| METHOD | 0 | 2 | 0 | 5 | 1 | 0 | 0 | 2 |
| RESULT | 0 | 3 | 0 | 2 | 5 | 0 | 0 | 0 |
| LIMITATION | 1 | 0 | 1 | 2 | 0 | 4 | 0 | 2 |
| NEXT_STEP | 1 | 0 | 1 | 0 | 1 | 0 | 4 | 2 |
| EXAMPLE | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 7 |

## Top Confusions For Best Model

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

## Interpretation

This is a transfer test: boundary-pair train/dev rows are added to training, but the locked fresh adjudicated test remains untouched. Improvements here indicate boundary-pair examples transfer beyond the synthetic boundary test.