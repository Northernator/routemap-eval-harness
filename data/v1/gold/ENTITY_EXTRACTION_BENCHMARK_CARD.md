# Entity Extraction Benchmark Card

## Purpose

Entity extraction is isolated here because role generalisation improved after boundary-pair training while strict full-row extraction remained at 0.000. The remaining bottleneck is not only role classification; exact entity-set prediction blocks strict full extraction and needs a separate benchmark lane.

## Data

- Train/dev reference source: `data/v1/gold/model_train_dev_role.csv`
- Fresh adjudicated test source: `data/v1/gold/model_test_fresh_adjudicated_role.csv`
- Rows evaluated: 79
- Current prediction source: `data/v1/gold/heldout_full_extraction_pred_v2_fresh_adjudicated.csv`
- Ontology baseline: `src/entity_ontology_v1.py`

## Results

| model | exact match | avg Jaccard | avg precision | avg recall | avg F1 | zero-overlap rows |
|---|---:|---:|---:|---:|---:|---:|
| current extractor | 0.025 | 0.326 | 0.638 | 0.373 | 0.452 | 12 |
| ontology_v1 | 0.076 | 0.506 | 0.759 | 0.589 | 0.634 | 5 |

Ontology v1 improves over the current extractor on exact match, average Jaccard, precision, recall, F1, and zero-overlap count. It wins on 49 rows, ties on 16 rows, loses on 9 rows, and both systems have zero overlap on 5 rows.

## Main Missing Entities For Ontology V1

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
| permission boundary | 4 |

## Main Extra Entities For Ontology V1

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

## Interpretation

The ontology baseline is clearly stronger than the current entity extractor on the locked fresh adjudicated test, but it is still not strong enough for strict full extraction. The main pattern is better recall for domain concepts at the cost of some extra broad entities, especially `retrieval`, `RouteMap`, and `governance`.

## Next Recommended Action

Keep this as the entity benchmark baseline. Next, improve entity extraction separately using train/dev data only: add train/dev-derived trigger coverage for missed concepts, test a learned multilabel baseline, and preserve the fresh adjudicated test as locked evaluation. Do not tune ontology triggers directly against these fresh-test errors.
