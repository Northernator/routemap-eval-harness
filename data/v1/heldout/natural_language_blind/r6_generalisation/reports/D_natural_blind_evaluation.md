# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 99 |
| missing/invalid rows | 0 |
| role accuracy | 0.343 |
| coarse_5 accuracy | 0.364 |
| coarse_4 accuracy | 0.364 |
| coarse_3 accuracy | 0.394 |
| entity exact match | 0.030 |
| entity average Jaccard | 0.235 |
| entity average precision | 0.459 |
| entity average recall | 0.285 |
| entity average F1 | 0.321 |
| operative status accuracy | 0.636 |
| relation accuracy | 0.333 |
| answer relevance accuracy | 0.889 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.040 |
| relaxed_2 | 0.061 |
| relaxed_3 | 0.061 |

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
| role+entity+status+relation | 32 |
| role+entity+relation | 31 |
| entity | 19 |
| entity+answer | 10 |
| entity+status | 3 |
| role+relation | 2 |
| answer | 1 |
| entity+status+relation | 1 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.