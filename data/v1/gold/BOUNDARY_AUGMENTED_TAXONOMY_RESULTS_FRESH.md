# Boundary-Augmented Taxonomy Results on Fresh Adjudicated Test

## Best Model Per Taxonomy

| taxonomy | setting | model | accuracy | previous_best | delta |
|---|---|---|---:|---:|---:|
| fine_8 | base_plus_boundary_train | centroid | 0.532 | 0.456 | +0.076 |
| coarse_5 | base_plus_boundary_train | centroid | 0.620 | 0.582 | +0.038 |
| coarse_4 | base_plus_boundary_train | centroid | 0.696 | 0.633 | +0.063 |
| coarse_3 | base_plus_boundary_train_dev | word_unigram_bigram_nb | 0.823 | 0.810 | +0.013 |

## All Scores

| setting | model | taxonomy | accuracy | delta |
|---|---|---|---:|---:|
| base_only | word_unigram_nb | fine_8 | 0.443 | -0.013 |
| base_only | word_unigram_nb | coarse_5 | 0.557 | -0.025 |
| base_only | word_unigram_nb | coarse_4 | 0.620 | -0.013 |
| base_only | word_unigram_nb | coarse_3 | 0.810 | +0.000 |
| base_only | word_unigram_bigram_nb | fine_8 | 0.443 | -0.013 |
| base_only | word_unigram_bigram_nb | coarse_5 | 0.557 | -0.025 |
| base_only | word_unigram_bigram_nb | coarse_4 | 0.633 | -0.000 |
| base_only | word_unigram_bigram_nb | coarse_3 | 0.810 | +0.000 |
| base_only | char_3_5gram_nb | fine_8 | 0.405 | -0.051 |
| base_only | char_3_5gram_nb | coarse_5 | 0.481 | -0.101 |
| base_only | char_3_5gram_nb | coarse_4 | 0.557 | -0.076 |
| base_only | char_3_5gram_nb | coarse_3 | 0.785 | -0.025 |
| base_only | centroid | fine_8 | 0.456 | -0.000 |
| base_only | centroid | coarse_5 | 0.582 | +0.000 |
| base_only | centroid | coarse_4 | 0.620 | -0.013 |
| base_only | centroid | coarse_3 | 0.797 | -0.013 |
| base_plus_boundary_train | word_unigram_nb | fine_8 | 0.456 | -0.000 |
| base_plus_boundary_train | word_unigram_nb | coarse_5 | 0.557 | -0.025 |
| base_plus_boundary_train | word_unigram_nb | coarse_4 | 0.595 | -0.038 |
| base_plus_boundary_train | word_unigram_nb | coarse_3 | 0.797 | -0.013 |
| base_plus_boundary_train | word_unigram_bigram_nb | fine_8 | 0.456 | -0.000 |
| base_plus_boundary_train | word_unigram_bigram_nb | coarse_5 | 0.570 | -0.012 |
| base_plus_boundary_train | word_unigram_bigram_nb | coarse_4 | 0.608 | -0.025 |
| base_plus_boundary_train | word_unigram_bigram_nb | coarse_3 | 0.823 | +0.013 |
| base_plus_boundary_train | char_3_5gram_nb | fine_8 | 0.418 | -0.038 |
| base_plus_boundary_train | char_3_5gram_nb | coarse_5 | 0.532 | -0.050 |
| base_plus_boundary_train | char_3_5gram_nb | coarse_4 | 0.608 | -0.025 |
| base_plus_boundary_train | char_3_5gram_nb | coarse_3 | 0.810 | +0.000 |
| base_plus_boundary_train | centroid | fine_8 | 0.532 | +0.076 |
| base_plus_boundary_train | centroid | coarse_5 | 0.620 | +0.038 |
| base_plus_boundary_train | centroid | coarse_4 | 0.696 | +0.063 |
| base_plus_boundary_train | centroid | coarse_3 | 0.823 | +0.013 |
| base_plus_boundary_train_dev | word_unigram_nb | fine_8 | 0.468 | +0.012 |
| base_plus_boundary_train_dev | word_unigram_nb | coarse_5 | 0.582 | +0.000 |
| base_plus_boundary_train_dev | word_unigram_nb | coarse_4 | 0.620 | -0.013 |
| base_plus_boundary_train_dev | word_unigram_nb | coarse_3 | 0.810 | +0.000 |
| base_plus_boundary_train_dev | word_unigram_bigram_nb | fine_8 | 0.430 | -0.026 |
| base_plus_boundary_train_dev | word_unigram_bigram_nb | coarse_5 | 0.570 | -0.012 |
| base_plus_boundary_train_dev | word_unigram_bigram_nb | coarse_4 | 0.620 | -0.013 |
| base_plus_boundary_train_dev | word_unigram_bigram_nb | coarse_3 | 0.823 | +0.013 |
| base_plus_boundary_train_dev | char_3_5gram_nb | fine_8 | 0.418 | -0.038 |
| base_plus_boundary_train_dev | char_3_5gram_nb | coarse_5 | 0.544 | -0.038 |
| base_plus_boundary_train_dev | char_3_5gram_nb | coarse_4 | 0.608 | -0.025 |
| base_plus_boundary_train_dev | char_3_5gram_nb | coarse_3 | 0.810 | +0.000 |
| base_plus_boundary_train_dev | centroid | fine_8 | 0.519 | +0.063 |
| base_plus_boundary_train_dev | centroid | coarse_5 | 0.608 | +0.026 |
| base_plus_boundary_train_dev | centroid | coarse_4 | 0.684 | +0.051 |
| base_plus_boundary_train_dev | centroid | coarse_3 | 0.823 | +0.013 |