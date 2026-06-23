# Entity Extraction Results on Fresh Adjudicated Test

| model | exact match | avg Jaccard | avg precision | avg recall | avg F1 | zero-overlap rows |
|---|---:|---:|---:|---:|---:|---:|
| pred_entities_current | 0.025 | 0.326 | 0.638 | 0.373 | 0.452 | 12 |
| pred_entities_ontology_v1 | 0.076 | 0.506 | 0.759 | 0.589 | 0.634 | 5 |

## pred_entities_current

### Most Common Missing Gold Entities

| entity | count |
|---|---:|
| evidence selection | 23 |
| model release governance | 14 |
| audit trail | 11 |
| tool-use security | 9 |
| answer support | 9 |
| consent boundary | 8 |
| source context | 8 |
| human review | 8 |
| policy context | 7 |
| risk management | 6 |
| retrieval trace | 6 |
| incident response | 5 |
| agent memory | 5 |
| RouteMap segment | 5 |
| AI safety evaluation | 4 |

### Most Common Extra Predicted Entities

| entity | count |
|---|---:|
| retrieval | 17 |
| RouteMap segment | 8 |
| audit | 8 |
| governance | 5 |
| source context | 4 |
| evaluation | 3 |
| documentation | 2 |
| monitoring | 2 |
| privacy | 2 |
| release evidence | 1 |
| secure AI development | 1 |
| human review | 1 |

## pred_entities_ontology_v1

### Most Common Missing Gold Entities

| entity | count |
|---|---:|
| evidence selection | 15 |
| model release governance | 9 |
| human review | 7 |
| source context | 7 |
| answer support | 7 |
| RouteMap segment | 6 |
| risk management | 5 |
| retrieval trace | 4 |
| privacy | 4 |
| tool-use security | 4 |
| permission boundary | 4 |
| agent memory | 4 |
| incident response | 4 |
| route extraction | 3 |
| route provenance | 3 |

### Most Common Extra Predicted Entities

| entity | count |
|---|---:|
| retrieval | 12 |
| RouteMap | 10 |
| governance | 7 |
| LLM application security | 5 |
| evaluation | 4 |
| RouteMap segment | 3 |
| human review | 2 |
| privacy | 1 |
| secure AI development | 1 |
| consent boundary | 1 |