# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 79 |
| missing/invalid rows | 0 |
| role accuracy | 0.532 |
| coarse_5 accuracy | 0.620 |
| coarse_4 accuracy | 0.696 |
| coarse_3 accuracy | 0.823 |
| entity exact match | 0.076 |
| entity average Jaccard | 0.506 |
| entity average precision | 0.759 |
| entity average recall | 0.589 |
| entity average F1 | 0.634 |
| operative status accuracy | 0.658 |
| relation accuracy | 0.430 |
| answer relevance accuracy | 0.848 |
| strict full-row accuracy | 0.025 |
| relaxed_1 | 0.253 |
| relaxed_2 | 0.354 |
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
| entity+relation | 14 |
| role+entity | 10 |
| entity+status+relation | 10 |
| entity | 9 |
| role+entity+status+relation | 8 |
| role+entity+relation | 7 |
| role+entity+answer | 4 |
| entity+answer | 3 |
| role+entity+status | 3 |
| none | 2 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.