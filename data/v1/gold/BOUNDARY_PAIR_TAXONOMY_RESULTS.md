# Boundary Pair Taxonomy Results

## Overall Accuracy

| setting | model | taxonomy | accuracy |
|---|---|---|---:|
| A_existing_train_dev | word_unigram_nb | fine_8 | 0.600 |
| A_existing_train_dev | word_unigram_nb | coarse_5 | 0.600 |
| A_existing_train_dev | word_unigram_nb | coarse_4 | 0.600 |
| A_existing_train_dev | word_unigram_nb | coarse_3 | 0.775 |
| A_existing_train_dev | word_unigram_bigram_nb | fine_8 | 0.575 |
| A_existing_train_dev | word_unigram_bigram_nb | coarse_5 | 0.600 |
| A_existing_train_dev | word_unigram_bigram_nb | coarse_4 | 0.600 |
| A_existing_train_dev | word_unigram_bigram_nb | coarse_3 | 0.825 |
| A_existing_train_dev | char_3_5gram_nb | fine_8 | 0.550 |
| A_existing_train_dev | char_3_5gram_nb | coarse_5 | 0.550 |
| A_existing_train_dev | char_3_5gram_nb | coarse_4 | 0.575 |
| A_existing_train_dev | char_3_5gram_nb | coarse_3 | 0.850 |
| A_existing_train_dev | simple_centroid_tfidf_like | fine_8 | 0.625 |
| A_existing_train_dev | simple_centroid_tfidf_like | coarse_5 | 0.650 |
| A_existing_train_dev | simple_centroid_tfidf_like | coarse_4 | 0.650 |
| A_existing_train_dev | simple_centroid_tfidf_like | coarse_3 | 0.825 |
| B_plus_boundary_train | word_unigram_nb | fine_8 | 0.950 |
| B_plus_boundary_train | word_unigram_nb | coarse_5 | 0.975 |
| B_plus_boundary_train | word_unigram_nb | coarse_4 | 0.975 |
| B_plus_boundary_train | word_unigram_nb | coarse_3 | 0.975 |
| B_plus_boundary_train | word_unigram_bigram_nb | fine_8 | 0.950 |
| B_plus_boundary_train | word_unigram_bigram_nb | coarse_5 | 0.975 |
| B_plus_boundary_train | word_unigram_bigram_nb | coarse_4 | 0.975 |
| B_plus_boundary_train | word_unigram_bigram_nb | coarse_3 | 0.975 |
| B_plus_boundary_train | char_3_5gram_nb | fine_8 | 0.950 |
| B_plus_boundary_train | char_3_5gram_nb | coarse_5 | 1.000 |
| B_plus_boundary_train | char_3_5gram_nb | coarse_4 | 1.000 |
| B_plus_boundary_train | char_3_5gram_nb | coarse_3 | 1.000 |
| B_plus_boundary_train | simple_centroid_tfidf_like | fine_8 | 0.950 |
| B_plus_boundary_train | simple_centroid_tfidf_like | coarse_5 | 0.950 |
| B_plus_boundary_train | simple_centroid_tfidf_like | coarse_4 | 0.950 |
| B_plus_boundary_train | simple_centroid_tfidf_like | coarse_3 | 0.975 |

## Best By Taxonomy

| taxonomy | setting | model | accuracy |
|---|---|---|---:|
| fine_8 | B_plus_boundary_train | word_unigram_nb | 0.950 |
| coarse_5 | B_plus_boundary_train | char_3_5gram_nb | 1.000 |
| coarse_4 | B_plus_boundary_train | char_3_5gram_nb | 1.000 |
| coarse_3 | B_plus_boundary_train | char_3_5gram_nb | 1.000 |