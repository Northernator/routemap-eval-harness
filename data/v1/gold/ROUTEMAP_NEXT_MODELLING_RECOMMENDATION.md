# RouteMap Next Modelling Recommendation

## Current Baseline

Best current 8-role score on the locked fresh adjudicated test set:

| model | accuracy |
|---|---:|
| simple_centroid_tfidf_like | 0.456 |

This is only a small improvement over the previous Naive Bayes baseline at 0.430.

## Grouped Taxonomy Results

| taxonomy | best model | best accuracy |
|---|---|---:|
| A: 8-role original | pred_centroid | 0.456 |
| B: 5-role compressed | pred_centroid | 0.582 |
| C: 4-role compressed | pred_word_unigram_bigram_nb | 0.633 |
| D: 3-role compressed | pred_word_unigram_nb | 0.810 |

The large jump under 4-role and 3-role mappings suggests the current 8-role taxonomy is too fine-grained for the present data and feature families. The model often detects broad function but misses fine role boundaries.

## Learning Curve

| model | all-data mean accuracy |
|---|---:|
| simple_centroid_tfidf_like | 0.456 |
| word_unigram_bigram_nb | 0.443 |

Accuracy rises as training size increases:

- Centroid: 0.238 at 20 rows, 0.413 at 120 rows, 0.456 with all 179 rows.
- Word unigram/bigram NB: 0.195 at 20 rows, 0.392 at 120 rows, 0.443 with all 179 rows.

This indicates more labelled data should help, but the all-data score is still low enough that data alone is unlikely to solve the 8-role problem quickly.

## Top Role-Pair Confusions

| gold_role | pred_role | count | likely boundary |
|---|---|---:|---|
| CLAIM | DEFINE | 3 | CLAIM_DEFINE_BOUNDARY |
| RESULT | CLAIM | 3 | RESULT_CLAIM_BOUNDARY |
| BACKGROUND | CLAIM | 2 | BACKGROUND_CLAIM_BOUNDARY |
| BACKGROUND | EXAMPLE | 2 | MULTIWAY_AMBIGUOUS |
| BACKGROUND | RESULT | 2 | MULTIWAY_AMBIGUOUS |

The errors are concentrated around semantic boundary distinctions rather than random noise. In particular, CLAIM/DEFINE, RESULT/CLAIM, and BACKGROUND/CLAIM need better modelling or clearer intermediate taxonomy.

## Recommendation

Recommended action: **E. all of the above in staged order**.

1. **Simplify taxonomy for an intermediate modelling target.** Use the 4-role taxonomy as the next diagnostic target because it preserves useful distinctions while improving to 0.633. Keep the 8-role labels as the long-term target.
2. **Collect more labelled data.** The learning curve is still rising, so more examples should help. Prioritize examples around CLAIM/DEFINE, RESULT/CLAIM, BACKGROUND/CLAIM, METHOD/EXAMPLE, and NEXT_STEP/METHOD.
3. **Use a stronger model or LLM classifier.** The standard-library models are useful controls, but 0.456 on the 8-role target is not strong enough. Test stronger learned encoders or carefully prompted LLM classifiers using only train/dev data for prompt and threshold iteration.
4. **Improve entity extraction separately.** Entity Jaccard remains poor in the full-extraction benchmark, and role improvements alone will not fix strict full-row accuracy.

Do not tune on the locked fresh adjudicated test set. Use the train/dev set for cross-validation, freeze modelling choices, then evaluate once on a new untouched split or the current locked test only when necessary.
