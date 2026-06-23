# FRESH_BLIND_V1_HEADLINE_REPORT

Frozen RouteMap-LLM role behavior holds, but full-row relaxed score drops on synthetic fresh_blind_v1. The binding constraint is the gap between entity coverage and full-row route/answer survival, with relaxed_3=0.006250 versus entity-only ceiling=0.012500.

## Gold Freeze

- SHA256: 552ed2c366217b2253dc2655e6c9d9d95c2aeaaf0812377fc5375da0cb4e79a9
- Rows: 160

## Role Accuracy

| model | taxonomy | accuracy |
| --- | --- | --- |
| RouteMap-LLM | fine_8 | 0.981250 |
| RouteMap-LLM | coarse_5 | 0.981250 |
| RouteMap-LLM | coarse_4 | 0.981250 |
| RouteMap-LLM | coarse_3 | 0.981250 |
| deterministic_baseline | fine_8 | 0.450000 |
| deterministic_baseline | coarse_5 | 0.562500 |
| deterministic_baseline | coarse_4 | 0.612500 |
| deterministic_baseline | coarse_3 | 0.756250 |

## Entity Quality

| model | exact_entity_avg_jaccard | soft_difflib_entity_avg_jaccard | soft_difflib_frac_jaccard_ge_0_5 | soft_embedding_entity_avg_jaccard | soft_embedding_frac_jaccard_ge_0_5 |
| --- | --- | --- | --- | --- | --- |
| RouteMap-LLM adaptive | 0.007872 | 0.019955 | 0.006250 | 0.023080 | 0.012500 |
| RouteMap-LLM open | 0.009658 | 0.019955 | 0.006250 | 0.023080 | 0.012500 |
| deterministic ontology | 0.000000 | 0.004167 | 0.000000 | 0.004167 | 0.000000 |

## Full Row Scores

| model | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | answer_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RouteMap-LLM | exact | 0.007872 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.950000 |
| RouteMap-LLM | soft-difflib | 0.019955 | 0.000000 | 0.006250 | 0.006250 | 0.006250 | 0.950000 |
| RouteMap-LLM | soft-embedding | 0.023080 | 0.000000 | 0.006250 | 0.006250 | 0.006250 | 0.950000 |
| deterministic_baseline | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.918750 |
| deterministic_baseline | soft-difflib | 0.004167 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.918750 |
| deterministic_baseline | soft-embedding | 0.004167 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.918750 |
| entity_only_ceiling | exact | 0.007872 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| entity_only_ceiling | soft-difflib | 0.019955 | 0.000000 | 0.006250 | 0.006250 | 0.006250 | 1.000000 |
| entity_only_ceiling | soft-embedding | 0.023080 | 0.000000 | 0.012500 | 0.012500 | 0.012500 | 1.000000 |

## Prior True-Blind Side By Side

| metric | prior_true_blind | fresh_blind_v1 |
| --- | --- | --- |
| role8 | 0.556000 | 0.981250 |
| coarse3 | 0.681000 | 0.981250 |
| relaxed_3_soft_embedding | 0.125000 | 0.006250 |
| entity_ceiling_relaxed3_soft_embedding | 0.181000 | 0.012500 |

## Caveat

fresh_blind_v1 is synthetic gold by construction. Treat it as an internal generalization check, then upgrade with independent human annotation via fresh_blind_annotation_template.csv or real external documents before publishing a credible headline.
