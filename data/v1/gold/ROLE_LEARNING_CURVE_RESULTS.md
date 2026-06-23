# Role Learning Curve Results

| model | train_size | mean_accuracy | min_accuracy | max_accuracy |
|---|---:|---:|---:|---:|
| simple_centroid_tfidf_like | 20 | 0.238 | 0.190 | 0.291 |
| simple_centroid_tfidf_like | 40 | 0.271 | 0.241 | 0.304 |
| simple_centroid_tfidf_like | 60 | 0.316 | 0.266 | 0.380 |
| simple_centroid_tfidf_like | 80 | 0.342 | 0.304 | 0.367 |
| simple_centroid_tfidf_like | 120 | 0.413 | 0.380 | 0.456 |
| simple_centroid_tfidf_like | all | 0.456 | 0.456 | 0.456 |
| word_unigram_bigram_nb | 20 | 0.195 | 0.152 | 0.228 |
| word_unigram_bigram_nb | 40 | 0.261 | 0.228 | 0.304 |
| word_unigram_bigram_nb | 60 | 0.263 | 0.228 | 0.304 |
| word_unigram_bigram_nb | 80 | 0.339 | 0.304 | 0.392 |
| word_unigram_bigram_nb | 120 | 0.392 | 0.354 | 0.430 |
| word_unigram_bigram_nb | all | 0.443 | 0.443 | 0.443 |

## Interpretation

If accuracy rises with more data, collect more labels. If accuracy plateaus low, improve features, model family, or taxonomy before collecting large amounts of similar data.