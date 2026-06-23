# Expanded Role Baseline Results V2

| testset | setting | model | fine_8 | coarse_5 | coarse_4 | coarse_3 |
|---|---|---|---:|---:|---:|---:|
| locked_fresh_adjudicated | old_train_only | word_unigram_nb | 0.443 | 0.557 | 0.620 | 0.810 |
| expanded_test_v2 | old_train_only | word_unigram_nb | 0.476 | 0.524 | 0.560 | 0.726 |
| locked_fresh_adjudicated | old_train_only | word_unigram_bigram_nb | 0.443 | 0.557 | 0.633 | 0.810 |
| expanded_test_v2 | old_train_only | word_unigram_bigram_nb | 0.405 | 0.500 | 0.536 | 0.774 |
| locked_fresh_adjudicated | old_train_only | char_3_5gram_nb | 0.405 | 0.481 | 0.557 | 0.785 |
| expanded_test_v2 | old_train_only | char_3_5gram_nb | 0.500 | 0.536 | 0.560 | 0.833 |
| locked_fresh_adjudicated | old_train_only | simple_centroid_tfidf_like | 0.456 | 0.582 | 0.620 | 0.797 |
| expanded_test_v2 | old_train_only | simple_centroid_tfidf_like | 0.405 | 0.512 | 0.536 | 0.702 |
| locked_fresh_adjudicated | old_plus_expanded_train | word_unigram_nb | 0.468 | 0.570 | 0.646 | 0.835 |
| expanded_test_v2 | old_plus_expanded_train | word_unigram_nb | 0.976 | 0.976 | 0.976 | 0.976 |
| locked_fresh_adjudicated | old_plus_expanded_train | word_unigram_bigram_nb | 0.506 | 0.608 | 0.671 | 0.835 |
| expanded_test_v2 | old_plus_expanded_train | word_unigram_bigram_nb | 0.988 | 0.988 | 0.988 | 0.988 |
| locked_fresh_adjudicated | old_plus_expanded_train | char_3_5gram_nb | 0.494 | 0.557 | 0.646 | 0.797 |
| expanded_test_v2 | old_plus_expanded_train | char_3_5gram_nb | 1.000 | 1.000 | 1.000 | 1.000 |
| locked_fresh_adjudicated | old_plus_expanded_train | simple_centroid_tfidf_like | 0.494 | 0.557 | 0.620 | 0.797 |
| expanded_test_v2 | old_plus_expanded_train | simple_centroid_tfidf_like | 1.000 | 1.000 | 1.000 | 1.000 |
| locked_fresh_adjudicated | old_plus_expanded_train_dev | word_unigram_nb | 0.456 | 0.519 | 0.608 | 0.797 |
| expanded_test_v2 | old_plus_expanded_train_dev | word_unigram_nb | 0.976 | 0.976 | 0.976 | 0.976 |
| locked_fresh_adjudicated | old_plus_expanded_train_dev | word_unigram_bigram_nb | 0.468 | 0.557 | 0.620 | 0.823 |
| expanded_test_v2 | old_plus_expanded_train_dev | word_unigram_bigram_nb | 0.988 | 0.988 | 0.988 | 0.988 |
| locked_fresh_adjudicated | old_plus_expanded_train_dev | char_3_5gram_nb | 0.506 | 0.582 | 0.671 | 0.797 |
| expanded_test_v2 | old_plus_expanded_train_dev | char_3_5gram_nb | 1.000 | 1.000 | 1.000 | 1.000 |
| locked_fresh_adjudicated | old_plus_expanded_train_dev | simple_centroid_tfidf_like | 0.468 | 0.519 | 0.582 | 0.772 |
| expanded_test_v2 | old_plus_expanded_train_dev | simple_centroid_tfidf_like | 1.000 | 1.000 | 1.000 | 1.000 |

## Best on locked_fresh_adjudicated

`old_plus_expanded_train_dev` / `char_3_5gram_nb` accuracy 0.506.

| gold | pred | count |
|---|---|---:|
| BACKGROUND | EXAMPLE | 2 |
| BACKGROUND | NEXT_STEP | 2 |
| CLAIM | EXAMPLE | 2 |
| CLAIM | LIMITATION | 2 |
| DEFINE | CLAIM | 2 |
| DEFINE | METHOD | 2 |
| METHOD | EXAMPLE | 2 |
| RESULT | EXAMPLE | 2 |
| LIMITATION | DEFINE | 2 |
| NEXT_STEP | EXAMPLE | 2 |

## Best on expanded_test_v2

`old_plus_expanded_train_dev` / `simple_centroid_tfidf_like` accuracy 1.000.

| gold | pred | count |
|---|---|---:|