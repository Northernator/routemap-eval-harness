# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 84 |
| missing/invalid rows | 0 |
| role accuracy | 0.476 |
| coarse_5 accuracy | 0.595 |
| coarse_4 accuracy | 0.619 |
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
| relaxed_1 | 0.179 |
| relaxed_2 | 0.274 |
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
| role+entity+status+relation | 24 |
| role+entity+relation | 7 |
| entity+answer | 7 |
| role+entity+status+relation+answer | 6 |
| role+entity+relation+answer | 5 |
| role+status+relation | 2 |
| none | 2 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.