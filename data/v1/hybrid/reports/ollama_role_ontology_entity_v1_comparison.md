# Hybrid Role/Ontology Entity Comparison

| variant | role acc | entity Jaccard | entity exact | relation acc | answer relevance | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ollama_full_v2 | 0.595 | 0.389 | 0.013 | 0.430 | 0.278 | 0.013 | 0.127 | 0.127 | 0.127 |
| ontology_v1_entity_baseline | 0.329 | 0.506 | 0.076 | 0.316 | 0.886 | 0.013 | 0.165 | 0.278 | 0.430 |
| combined_v3 | 0.532 | 0.506 | 0.076 | 0.443 | 0.848 | 0.051 | 0.253 | 0.354 | 0.443 |
| ollama_role_ontology_entity_v1 | 0.595 | 0.506 | 0.076 | 0.430 | 0.278 | 0.013 | 0.177 | 0.177 | 0.190 |

## Interpretation

The hybrid preserves Ollama role accuracy at 0.595 versus Ollama full v2 0.595.
Entity Jaccard moves from Ollama full v2 0.389 toward ontology_v1 at 0.506.
Relaxed_1 changes from 0.127 to 0.177; combined_v3 remains 0.253.