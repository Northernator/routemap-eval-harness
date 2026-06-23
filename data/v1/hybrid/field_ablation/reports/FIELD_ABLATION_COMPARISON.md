# Field Ablation Comparison

## Metrics

| variant | role | entity_jaccard | entity_exact | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ollama_full_v2 | 0.595 | 0.389 | 0.013 | 0.658 | 0.430 | 0.278 | 0.013 | 0.127 | 0.127 | 0.127 |
| ontology_v1_entity_baseline | 0.329 | 0.506 | 0.076 |  | 0.316 | 0.886 | 0.013 | 0.165 | 0.278 | 0.430 |
| combined_v3 | 0.532 | 0.506 | 0.076 |  | 0.443 | 0.848 | 0.051 | 0.253 | 0.354 | 0.443 |
| previous_hybrid_ollama_role_ontology_entity | 0.595 | 0.506 | 0.076 | 0.658 | 0.430 | 0.278 | 0.013 | 0.177 | 0.177 | 0.190 |
| A_ollama_role_ontology_entities_ollama_other | 0.595 | 0.506 | 0.076 | 0.658 | 0.430 | 0.278 | 0.013 | 0.177 | 0.177 | 0.190 |
| B_add_combined_status | 0.595 | 0.506 | 0.076 | 0.595 | 0.430 | 0.278 | 0.013 | 0.177 | 0.177 | 0.190 |
| C_add_combined_relation | 0.595 | 0.506 | 0.076 | 0.658 | 0.443 | 0.278 | 0.013 | 0.177 | 0.177 | 0.190 |
| D_add_combined_answer | 0.595 | 0.506 | 0.076 | 0.658 | 0.430 | 0.848 | 0.025 | 0.304 | 0.304 | 0.316 |
| E_combined_status_relation_answer | 0.595 | 0.506 | 0.076 | 0.595 | 0.443 | 0.848 | 0.025 | 0.304 | 0.304 | 0.316 |

## Interpretation

Previous hybrid relaxed scores were 0.177 / 0.177 / 0.190.
Variant E relaxed scores are 0.304 / 0.304 / 0.316.
Combined_v3 relaxed scores are 0.253 / 0.354 / 0.443.
Best relaxed_1: D_add_combined_answer = 0.304.
Best relaxed_2: combined_v3 = 0.354.
Best relaxed_3: combined_v3 = 0.443.
