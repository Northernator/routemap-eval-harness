# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 79 |
| missing/invalid rows | 0 |
| role accuracy | 0.595 |
| coarse_5 accuracy | 0.595 |
| coarse_4 accuracy | 0.595 |
| coarse_3 accuracy | 0.608 |
| entity exact match | 0.013 |
| entity average Jaccard | 0.389 |
| entity average precision | 0.660 |
| entity average recall | 0.418 |
| entity average F1 | 0.503 |
| operative status accuracy | 0.658 |
| relation accuracy | 0.430 |
| answer relevance accuracy | 0.278 |
| strict full-row accuracy | 0.013 |
| relaxed_1 | 0.127 |
| relaxed_2 | 0.127 |
| relaxed_3 | 0.127 |

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
| entity | 16 |
| role+entity+status+relation+answer | 16 |
| role+entity+relation+answer | 15 |
| entity+answer | 12 |
| entity+status+relation+answer | 6 |
| entity+status+answer | 5 |
| entity+relation | 4 |
| entity+relation+answer | 3 |
| none | 1 |
| role+entity+relation | 1 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.