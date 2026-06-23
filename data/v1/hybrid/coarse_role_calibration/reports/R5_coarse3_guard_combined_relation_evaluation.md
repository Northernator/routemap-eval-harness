# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 79 |
| missing/invalid rows | 0 |
| role accuracy | 0.709 |
| coarse_5 accuracy | 0.734 |
| coarse_4 accuracy | 0.772 |
| coarse_3 accuracy | 0.823 |
| entity exact match | 0.076 |
| entity average Jaccard | 0.506 |
| entity average precision | 0.759 |
| entity average recall | 0.589 |
| entity average F1 | 0.634 |
| operative status accuracy | 0.658 |
| relation accuracy | 0.443 |
| answer relevance accuracy | 0.848 |
| strict full-row accuracy | 0.038 |
| relaxed_1 | 0.354 |
| relaxed_2 | 0.392 |
| relaxed_3 | 0.443 |

## Local Baselines

| baseline | score |
|---|---:|
| best local fine_8 role | 0.532 |
| ontology_v1 entity Jaccard | 0.506 |
| combined_v3 strict | 0.051 |
| combined_v3 relaxed_1 | 0.253 |
| combined_v3 relaxed_2 | 0.354 |
| combined_v3 relaxed_3 | 0.443 |

## Top Failure Patterns

| pattern | rows |
|---|---:|
| entity | 20 |
| entity+relation | 15 |
| role+entity+status+relation | 9 |
| entity+status | 7 |
| entity+status+relation | 6 |
| role+entity+relation+answer | 5 |
| role+entity+relation | 5 |
| entity+answer | 3 |
| none | 3 |
| role+entity+status+relation+answer | 3 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.