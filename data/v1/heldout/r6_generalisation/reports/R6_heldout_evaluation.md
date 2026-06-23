# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 84 |
| missing/invalid rows | 0 |
| role accuracy | 0.595 |
| coarse_5 accuracy | 0.655 |
| coarse_4 accuracy | 0.679 |
| coarse_3 accuracy | 0.833 |
| entity exact match | 0.048 |
| entity average Jaccard | 0.459 |
| entity average precision | 0.590 |
| entity average recall | 0.710 |
| entity average F1 | 0.613 |
| operative status accuracy | 0.619 |
| relation accuracy | 0.476 |
| answer relevance accuracy | 0.786 |
| strict full-row accuracy | 0.024 |
| relaxed_1 | 0.262 |
| relaxed_2 | 0.310 |
| relaxed_3 | 0.345 |

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
| entity | 31 |
| role+entity+status+relation | 19 |
| entity+answer | 7 |
| role+entity+status+relation+answer | 6 |
| role+entity+relation+answer | 5 |
| entity+status+relation | 5 |
| role+entity+relation | 4 |
| entity+relation | 3 |
| status+relation | 2 |
| none | 2 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.