# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 79 |
| missing/invalid rows | 0 |
| role accuracy | 0.127 |
| coarse_5 accuracy | 0.127 |
| coarse_4 accuracy | 0.127 |
| coarse_3 accuracy | 0.127 |
| entity exact match | 0.000 |
| entity average Jaccard | 0.000 |
| entity average precision | 0.000 |
| entity average recall | 0.000 |
| entity average F1 | 0.000 |
| operative status accuracy | 0.506 |
| relation accuracy | 0.127 |
| answer relevance accuracy | 0.038 |
| strict full-row accuracy | 0.000 |
| relaxed_1 | 0.000 |
| relaxed_2 | 0.000 |
| relaxed_3 | 0.000 |

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
| role+entity+status+relation+answer | 39 |
| role+entity+relation+answer | 30 |
| entity+answer | 7 |
| entity | 3 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.