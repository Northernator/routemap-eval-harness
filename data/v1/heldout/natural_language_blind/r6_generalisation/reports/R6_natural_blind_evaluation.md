# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 99 |
| missing/invalid rows | 0 |
| role accuracy | 0.939 |
| coarse_5 accuracy | 0.960 |
| coarse_4 accuracy | 0.960 |
| coarse_3 accuracy | 0.990 |
| entity exact match | 0.030 |
| entity average Jaccard | 0.235 |
| entity average precision | 0.459 |
| entity average recall | 0.285 |
| entity average F1 | 0.321 |
| operative status accuracy | 0.970 |
| relation accuracy | 0.889 |
| answer relevance accuracy | 0.889 |
| strict full-row accuracy | 0.010 |
| relaxed_1 | 0.152 |
| relaxed_2 | 0.172 |
| relaxed_3 | 0.172 |

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
| entity | 70 |
| entity+answer | 10 |
| entity+relation | 9 |
| role+entity | 5 |
| entity+status | 2 |
| none | 1 |
| role+status+relation+answer | 1 |
| relation | 1 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.