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
| entity exact match | 0.076 |
| entity average Jaccard | 0.506 |
| entity average precision | 0.759 |
| entity average recall | 0.589 |
| entity average F1 | 0.634 |
| operative status accuracy | 0.658 |
| relation accuracy | 0.430 |
| answer relevance accuracy | 0.848 |
| strict full-row accuracy | 0.025 |
| relaxed_1 | 0.304 |
| relaxed_2 | 0.304 |
| relaxed_3 | 0.316 |

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
| entity | 19 |
| role+entity+relation | 14 |
| role+entity+status+relation | 13 |
| entity+answer | 7 |
| entity+relation | 7 |
| entity+status+relation | 5 |
| entity+status | 4 |
| none | 2 |
| role+status+relation | 2 |
| answer | 1 |

## Interpretation

Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.