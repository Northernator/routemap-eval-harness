# RouteMap v1 Generalisation Baseline Report

## Experiment Ladder

### 1. Seed Role Baseline

| run | accuracy |
|---|---:|
| sample_role | 0.414 |
| v2 heading-aware role | 1.000 |
| v2 no-leak role | 0.525 |
| v3 no-leak role on seed | 1.000 |

Interpretation: the seed result was overfit and strongly dependent on headings and familiar wording. Perfect seed accuracy was not evidence of semantic role generalisation.

### 2. Held-Out Role v1

| run | accuracy |
|---|---:|
| v3 held-out role | 0.450 |

Interpretation: semantic role generalisation was weak once the classifier saw unseen held-out wording.

### 3. Held-Out Full Extraction v1

| metric | score |
|---|---:|
| Role accuracy | 0.450 |
| Operative status accuracy | 0.613 |
| Relation accuracy | 0.438 |
| Answer relevance accuracy | 0.875 |
| Entity exact match | 0.300 |
| Entity average Jaccard | 0.405 |
| Strict full-row accuracy | 0.113 |

### 4. Tuned Development-Set v2

| metric | score |
|---|---:|
| Role accuracy | 0.988 |
| Operative status accuracy | 1.000 |
| Relation accuracy | 0.875 |
| Answer relevance accuracy | 1.000 |
| Entity exact match | 0.500 |
| Entity average Jaccard | 0.712 |
| Strict full-row accuracy | 0.475 |

Warning: this result was tuned from held-out v1 errors, so it is development-set performance only.

### 5. Fresh Held-Out v2

| metric | score |
|---|---:|
| Role accuracy | 0.325 |
| Operative status accuracy | 0.500 |
| Relation accuracy | 0.312 |
| Answer relevance accuracy | 0.887 |
| Entity exact match | 0.013 |
| Entity average Jaccard | 0.284 |
| Strict full-row accuracy | 0.000 |

Interpretation: the v2 extractor overfit the development set and collapsed on fresh held-out wording.

### 6. Adjudicated Fresh Held-Out v2

| item | value |
|---|---:|
| Included rows | 79 |
| Excluded rows | 1 |
| Rule v2 role accuracy | 0.329 |
| Naive Bayes role accuracy | 0.430 |
| Hybrid role accuracy | 0.418 |
| Full strict row accuracy | 0.000 |
| Entity average Jaccard | 0.283 |

Interpretation: adjudication did not materially change the conclusion. The labels mostly held; model generalisation is the real bottleneck.

## Conclusion

The route extraction pipeline is working technically: it can build gold files, run predictors, evaluate full extraction, adjudicate labels, exclude unresolved rows, and compare baselines reproducibly.

The current deterministic and rule-based extractors are not robust. They can improve sharply on a development set, but the improvement does not survive fresh held-out wording. Naive Bayes is the best current role baseline, but its adjudicated fresh-test accuracy is still weak at 0.430.

Answer relevance is the easiest subtask so far. Entity extraction and semantic role classification are the next bottlenecks, and role errors continue to cascade into relation and operative-status errors.

The next phase should test stronger learned baselines without using the adjudicated fresh test set for tuning. The fresh adjudicated set should remain locked as a final generalisation check.
