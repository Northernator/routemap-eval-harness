# FRESH_BLIND_V2_HEADLINE_REPORT

fresh_blind_v2 role read is plausible with role8=0.706250; full-row soft relaxed_3=0.106250 versus entity ceiling=0.131250.

## Validation Gate

| verbatim_entity_rate | banned_marker_hit_rate | entity_vocab_diversity | telegraph_probe_8role_accuracy |
| --- | --- | --- | --- |
| 1.000000 | 0.000000 | 0.500000 | 0.875000 |

## Credibility Readout

| telegraph_probe_lexical_baseline_role8 | llm_role8_minus_lexical_baseline_role8 | plausibility_flag |
| --- | --- | --- |
| 0.875000 | -0.168750 | plausible |

## Role Accuracy

| model | taxonomy | accuracy |
| --- | --- | --- |
| RouteMap-LLM | fine_8 | 0.706250 |
| RouteMap-LLM | coarse_5 | 0.762500 |
| RouteMap-LLM | coarse_4 | 0.793750 |
| RouteMap-LLM | coarse_3 | 0.862500 |
| lexical_baseline | fine_8 | 0.875000 |
| lexical_baseline | coarse_5 | 0.887500 |
| lexical_baseline | coarse_4 | 0.900000 |
| lexical_baseline | coarse_3 | 0.943750 |

## Entity Quality

| model | exact_entity_avg_jaccard | soft_embedding_entity_avg_jaccard | soft_embedding_frac_jaccard_ge_0_5 | pred_verbatim_rate | empty_row_count |
| --- | --- | --- | --- | --- | --- |
| repaired_fallback | 0.105799 | 0.314410 | 0.131250 | 0.859335 | 0.000000 |
| llm_open | 0.071979 | 0.111563 | 0.131250 | 1.000000 | 137.000000 |
| ontology | 0.000000 | 0.008333 | 0.000000 | 0.066667 | 137.000000 |

## Full Row Scores

| model | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | answer_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RouteMap-LLM | exact | 0.105799 | 0.025000 | 0.037500 | 0.037500 | 0.037500 | 0.918750 |
| RouteMap-LLM | soft-difflib | 0.285104 | 0.037500 | 0.106250 | 0.106250 | 0.106250 | 0.918750 |
| RouteMap-LLM | soft-embedding | 0.314410 | 0.037500 | 0.106250 | 0.106250 | 0.106250 | 0.918750 |
| lexical_baseline | exact | 0.105799 | 0.025000 | 0.050000 | 0.050000 | 0.050000 | 0.931250 |
| lexical_baseline | soft-difflib | 0.285104 | 0.037500 | 0.112500 | 0.112500 | 0.118750 | 0.931250 |
| lexical_baseline | soft-embedding | 0.314410 | 0.037500 | 0.112500 | 0.112500 | 0.118750 | 0.931250 |
| entity_only_ceiling | exact | 0.105799 | 0.031250 | 0.062500 | 0.062500 | 0.062500 | 1.000000 |
| entity_only_ceiling | soft-difflib | 0.285104 | 0.050000 | 0.131250 | 0.131250 | 0.131250 | 1.000000 |
| entity_only_ceiling | soft-embedding | 0.314410 | 0.056250 | 0.131250 | 0.131250 | 0.131250 | 1.000000 |

## Comparison

| source | role8 | coarse3 | relaxed_3 | entity_ceiling |
| --- | --- | --- | --- | --- |
| prior_true_blind | 0.556000 | 0.681000 | 0.125000 | 0.181000 |
| fresh_blind_v1 | 0.981000 | 0.981000 | 0.006250 | 0.012500 |
| fresh_blind_v2 | 0.706250 | 0.862500 | 0.106250 | 0.131250 |

## Caveat

fresh_blind_v2 is still synthetic gold. Treat it as an artifact probe and internal generalization check; upgrade through independent human annotation or real external documents before reporting a credible benchmark.
