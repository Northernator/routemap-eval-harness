# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 84 |
| missing/invalid rows | 0 |
| role accuracy | 0.500 |
| coarse_5 accuracy | 0.500 |
| coarse_4 accuracy | 0.500 |
| coarse_3 accuracy | 0.512 |
| entity exact match | 0.048 |
| entity average Jaccard | 0.459 |
| entity average precision | 0.590 |
| entity average recall | 0.710 |
| entity average F1 | 0.613 |
| operative status accuracy | 0.667 |
| relation accuracy | 0.476 |
| answer relevance accuracy | 0.786 |
| strict full-row accuracy | 0.036 |
| relaxed_1 | 0.167 |
| relaxed_2 | 0.167 |
| relaxed_3 | 0.167 |

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
| role+entity+status+relation | 20 |
| entity | 19 |
| role+entity+relation | 17 |
| entity+answer | 12 |
| role+entity+relation+answer | 4 |
| entity+status | 4 |
| none | 3 |
| entity+status+relation | 2 |
| entity+status+answer | 2 |
| role+relation | 1 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.