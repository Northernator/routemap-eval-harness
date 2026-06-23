# full_extraction_with_v2_entities

Development read. V2 entities are frozen via extract_entities_hybrid_v2 module constants. Allowed dev and frozen true-blind prediction copies only; locked fresh/adjudicated test files were not read or modified.

Prior context: strict full-row was 0.000 on true-blind exact scoring; ontology_v1 in-domain entity Jaccard context was 0.506.

## in_domain_dev

| variant | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0_pred_entities | exact | 0.719792 | 0.487500 | 0.837500 | 0.837500 | 0.837500 | 0.987500 |
| V0_pred_entities | soft-difflib | 0.711667 | 0.475000 | 0.837500 | 0.837500 | 0.837500 | 0.987500 |
| V0_pred_entities | soft-embedding | 0.714345 | 0.475000 | 0.837500 | 0.837500 | 0.837500 | 0.987500 |
| V_ontology | exact | 0.452083 | 0.225000 | 0.525000 | 0.525000 | 0.525000 | 0.987500 |
| V_ontology | soft-difflib | 0.469345 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 |
| V_ontology | soft-embedding | 0.465179 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 |
| V2 | exact | 0.452083 | 0.225000 | 0.525000 | 0.525000 | 0.525000 | 0.987500 |
| V2 | soft-difflib | 0.472991 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 |
| V2 | soft-embedding | 0.474702 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 |
| DIAGNOSTIC_gold_other_V2 | exact | 0.452083 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 1.000000 |
| DIAGNOSTIC_gold_other_V2 | soft-difflib | 0.472991 | 0.275000 | 0.550000 | 0.550000 | 0.550000 | 1.000000 |
| DIAGNOSTIC_gold_other_V2 | soft-embedding | 0.474702 | 0.275000 | 0.550000 | 0.550000 | 0.550000 | 1.000000 |

## true_blind_combined_v3

| variant | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0_pred_entities | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V0_pred_entities | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V0_pred_entities | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V_ontology | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V_ontology | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V_ontology | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V2 | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V2 | soft-difflib | 0.127552 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V2 | soft-embedding | 0.170211 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| DIAGNOSTIC_gold_other_V2 | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| DIAGNOSTIC_gold_other_V2 | soft-difflib | 0.127552 | 0.000000 | 0.013889 | 0.013889 | 0.013889 | 1.000000 |
| DIAGNOSTIC_gold_other_V2 | soft-embedding | 0.170211 | 0.000000 | 0.027778 | 0.027778 | 0.027778 | 1.000000 |

## true_blind_R6

| variant | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0_pred_entities | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V0_pred_entities | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V0_pred_entities | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V_ontology | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V_ontology | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V_ontology | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V2 | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V2 | soft-difflib | 0.127552 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| V2 | soft-embedding | 0.170211 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 |
| DIAGNOSTIC_gold_other_V2 | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| DIAGNOSTIC_gold_other_V2 | soft-difflib | 0.127552 | 0.000000 | 0.013889 | 0.013889 | 0.013889 | 1.000000 |
| DIAGNOSTIC_gold_other_V2 | soft-embedding | 0.170211 | 0.000000 | 0.027778 | 0.027778 | 0.027778 | 1.000000 |

## Role Accuracy Constant Check

| dataset | role_accuracy_constant |
| --- | --- |
| in_domain_dev | 1.000000 |
| true_blind_combined_v3 | 1.000000 |
| true_blind_R6 | 1.000000 |

## Verdicts

| in_domain_no_regression | soft_metric_unlocks_transfer | entities_sufficient_for_relaxed | strict_moves |
| --- | --- | --- | --- |
| 1.000000 | 0.000000 | 0.000000 | 1.000000 |

## Recommendation

V2 entity swap does not unlock full-row relaxed scores enough; keep entity metric/extractor development ahead of route-field work.