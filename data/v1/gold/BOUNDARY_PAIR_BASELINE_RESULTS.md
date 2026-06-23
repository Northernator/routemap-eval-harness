# Boundary Pair Baseline Results

- Boundary train rows: 120
- Boundary dev rows: 40
- Boundary test rows: 40

## Accuracy By Setting And Model

| setting | model | accuracy |
|---|---|---:|
| A_existing_train_dev | word_unigram_nb | 0.600 |
| A_existing_train_dev | word_unigram_bigram_nb | 0.575 |
| A_existing_train_dev | char_3_5gram_nb | 0.550 |
| A_existing_train_dev | simple_centroid_tfidf_like | 0.625 |
| B_plus_boundary_train | word_unigram_nb | 0.950 |
| B_plus_boundary_train | word_unigram_bigram_nb | 0.950 |
| B_plus_boundary_train | char_3_5gram_nb | 0.950 |
| B_plus_boundary_train | simple_centroid_tfidf_like | 0.950 |

## Top Confusion Pairs

### A_existing_train_dev: simple_centroid_tfidf_like

| gold | pred | count |
|---|---|---:|
| CLAIM | BACKGROUND | 3 |
| EXAMPLE | DEFINE | 2 |
| CLAIM | METHOD | 1 |
| CLAIM | NEXT_STEP | 1 |
| DEFINE | BACKGROUND | 1 |
| CLAIM | EXAMPLE | 1 |
| BACKGROUND | EXAMPLE | 1 |
| BACKGROUND | DEFINE | 1 |
| METHOD | DEFINE | 1 |
| METHOD | BACKGROUND | 1 |

### B_plus_boundary_train: word_unigram_nb

| gold | pred | count |
|---|---|---:|
| DEFINE | BACKGROUND | 1 |
| DEFINE | RESULT | 1 |

## Interpretation

Best Setting A: `simple_centroid_tfidf_like` at 0.625.
Best Setting B: `word_unigram_nb` at 0.950.
Adding boundary-pair training data changed boundary-pair test accuracy by +0.325.