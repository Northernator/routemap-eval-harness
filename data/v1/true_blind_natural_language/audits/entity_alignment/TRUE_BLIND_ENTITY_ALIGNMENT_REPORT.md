# True-Blind Entity Alignment Audit

This is audit-only. It does not modify gold, predictions, evaluator logic, prompts, models, taxonomies, or thresholds.

## Answers

| question | answer |
|---|---|
| A. Why did entity Jaccard collapse to zero? | Gold entities are JSON-list freeform strings, while the evaluator expects semicolon-delimited entity strings and predictions are ontology_v1 canonical labels. Current parser reads each JSON list as one unmatched entity. |
| B. Are predictions empty, parsed wrong, or semantically misaligned? | Mixed: predictions are non-empty on only a subset of rows and parse correctly when present; non-empty predictions are ontology labels that mostly do not overlap freeform gold labels. |
| C. Are gold entities in a different format from ontology_v1? | Yes. Gold uses JSON lists of domain-specific phrases; ontology_v1 has 31 broad canonical RouteMap/AI-governance labels. |
| D. Are true-blind gold entities too freeform compared with previous gold? | Yes for current evaluator assumptions; labels name local domain objects rather than ontology_v1 canonical concepts. |
| E. Would simple normalisation fix anything? | No meaningful fix: lowercase/trim and punctuation stripping do not create overlap. |
| F. Would alias mapping fix anything? | Only low-confidence cooccurrence aliases are available; no high/medium safe aliases should be auto-applied. |
| G. Is an ontology expansion needed? | Yes, or a separate true-blind entity canonicalisation/adjudication pass mapping freeform gold to ontology_v1. |
| H. Is the evaluator reading the correct columns? | Yes: gold_entities and pred_entities. The failure is representation/ontology alignment, not wrong column selection. |
| I. What is the safest next ablation? | Freeze predictions, create a separate proposed canonicalised gold set via human-reviewed ontology mapping, then rerun scoring as a labelled ablation without replacing this benchmark. |

## Entity Column Summary

| measure | value |
|---|---|
| row count | 72 |
| non-empty gold entity rows | 72 |
| unique gold entities | 337 |
| gold parse failures | 0 |

## Prediction Entity Summary

| variant | non-empty rows | parse failures | unique predicted entities |
|---|---|---|---|
| combined | 17 | 0 | 7 |
| D | 17 | 0 | 7 |
| R6 | 17 | 0 | 7 |

## Raw Overlap

| variant | avg current Jaccard | rows any overlap | rows exact |
|---|---|---|---|
| combined | 0.000000 | 0 | 0 |
| D | 0.000000 | 0 | 0 |
| R6 | 0.000000 | 0 | 0 |

## Normalised Overlap

| variant | lower avg J | punct avg J | alias avg J | lower improved rows | punct improved rows | alias improved rows |
|---|---|---|---|---|---|---|
| combined | 0.005556 | 0.005556 | 0.014583 | 1 | 1 | 4 |
| D | 0.005556 | 0.005556 | 0.014583 | 1 | 1 | 4 |
| R6 | 0.005556 | 0.005556 | 0.014583 | 1 | 1 | 4 |

## Mismatch Buckets

| bucket | rows |
|---|---|
| empty_prediction_entities | 55 |
| delimiter_format_mismatch | 13 |
| singular_plural_or_alias_mismatch | 4 |

## Top Missing Gold Entities

| gold entity | count | example segment_ids |
|---|---|---|
| route classifier | 2 | TB006; TB053 |
| exception | 2 | TB009; TB012 |
| urgency | 2 | TB013; TB063 |
| queue | 2 | TB017; TB064 |
| engineer notes | 2 | TB020; TB024 |
| model | 2 | TB023; TB066 |
| blind set | 2 | TB024; TB066 |
| approver | 2 | TB032; TB036 |
| trial | 2 | TB041; TB071 |
| review | 2 | TB053; TB065 |

## Top Predicted-Only Entities

| predicted entity | count | example segment_ids |
|---|---|---|
| controls | 7 | TB031; TB032; TB033; TB034; TB035 |
| evaluation | 4 | TB018; TB042; TB060; TB066 |
| human review | 3 | TB030; TB032; TB046 |
| incident response | 1 | TB001 |
| permission boundary | 1 | TB004 |
| benchmark | 1 | TB048 |

## Alias Candidates

Candidate alias rows: 91. Low-confidence aliases are not auto-applied.
