# LLM Extraction Evaluation

## Metrics

| metric | value |
|---|---:|
| evaluated rows | 5 |
| missing/invalid rows | 74 |
| role accuracy | 1.000 |
| coarse_5 accuracy | 1.000 |
| coarse_4 accuracy | 1.000 |
| coarse_3 accuracy | 1.000 |
| entity exact match | 1.000 |
| entity average Jaccard | 1.000 |
| entity average precision | 1.000 |
| entity average recall | 1.000 |
| entity average F1 | 1.000 |
| operative status accuracy | 1.000 |
| relation accuracy | 1.000 |
| answer relevance accuracy | 1.000 |
| strict full-row accuracy | 1.000 |
| relaxed_1 | 1.000 |
| relaxed_2 | 1.000 |
| relaxed_3 | 1.000 |

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
| none | 5 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.