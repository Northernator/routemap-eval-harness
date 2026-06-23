# Expanded Entity Baseline Results V2

| testset | model | exact | Jaccard | precision | recall | F1 | zero overlap |
|---|---|---:|---:|---:|---:|---:|---:|
| locked_fresh_adjudicated | current_extractor_v2 | 0.025 | 0.326 | 0.638 | 0.373 | 0.452 | 12 |
| locked_fresh_adjudicated | ontology_v1 | 0.076 | 0.506 | 0.759 | 0.589 | 0.634 | 5 |
| locked_fresh_adjudicated | expanded_gazetteer | 0.051 | 0.429 | 0.812 | 0.432 | 0.545 | 14 |
| expanded_test_v2 | current_extractor_v2 | 0.024 | 0.344 | 0.477 | 0.528 | 0.481 | 6 |
| expanded_test_v2 | ontology_v1 | 0.048 | 0.459 | 0.590 | 0.710 | 0.613 | 0 |
| expanded_test_v2 | expanded_gazetteer | 0.107 | 0.587 | 0.785 | 0.706 | 0.724 | 0 |