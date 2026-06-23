# Held-Out Full Extraction Error Analysis

## Executive Summary

- Total rows: 80
- Role accuracy: 0.988
- Operative status accuracy: 1.000
- Relation accuracy: 0.875
- Answer relevance accuracy: 1.000
- Entity exact match: 0.500
- Entity average Jaccard: 0.712
- Strict full-row accuracy: 0.475
- Strict mismatch rows: 42

## Biggest Bottlenecks

- Role errors are the main upstream failure, especially overprediction of `CLAIM`.
- Relation and operative-status errors often cascade from wrong role predictions.
- Entity extraction has low exact match and many zero-overlap rows, showing that held-out entity wording is not covered by the current prediction heuristic.
- Answer relevance is comparatively strong but still fails for background rows predicted as answer-bearing roles.

## Role Confusion Matrix

| gold | pred | count |
|---|---|---:|
| BACKGROUND | BACKGROUND | 10 |
| CLAIM | CLAIM | 9 |
| CLAIM | LIMITATION | 1 |
| DEFINE | DEFINE | 10 |
| EXAMPLE | EXAMPLE | 10 |
| LIMITATION | LIMITATION | 10 |
| METHOD | METHOD | 10 |
| NEXT_STEP | NEXT_STEP | 10 |
| RESULT | RESULT | 10 |

## Top Role Confusion Pairs

| gold_role | pred_role | count |
|---|---|---:|
| CLAIM | LIMITATION | 1 |

## Relation Confusion Matrix

| gold | pred | count |
|---|---|---:|
| asserts | asserts | 9 |
| asserts | limits | 1 |
| defines | defines | 10 |
| gives_example | gives_example | 10 |
| limits | limits | 5 |
| maps_to | recommends | 5 |
| proposes_next_test | proposes_next_test | 10 |
| recommends | recommends | 5 |
| reports_usefulness | reports_usefulness | 6 |
| sets_context | sets_context | 10 |
| supports_retrieval | reports_usefulness | 4 |
| warns_about | warns_about | 5 |

## Operative Status Confusion Matrix

| gold | pred | count |
|---|---|---:|
| ACTIVE | ACTIVE | 29 |
| DESCRIPTIVE | DESCRIPTIVE | 40 |
| LIMITED | LIMITED | 5 |
| NEGATED | NEGATED | 6 |

## Entity Diagnostics

- Rows with exact entity match: 40
- Rows with partial entity overlap: 33
- Rows with zero entity overlap: 7

### Most Common Missing Gold Entities

| entity | count |
|---|---:|
| evaluation | 10 |
| routemap segment | 5 |
| permission boundary | 4 |
| privacy | 1 |
| route extraction | 1 |
| source context | 1 |
| llm application security | 1 |

### Most Common Extra Predicted Entities

| entity | count |
|---|---:|
| routemap segment | 10 |
| benchmark | 5 |
| monitoring | 4 |
| retrieval | 4 |
| llm application security | 2 |
| governance | 2 |
| controls | 2 |
| answer support | 2 |
| fairness | 2 |
| nist ai rmf | 1 |

## Strict Mismatch Clusters

| failure_pattern | count |
|---|---:|
| none | 38 |
| entity | 32 |
| relation+entity | 8 |
| role+relation | 1 |
| relation | 1 |

## Examples: Top Role Errors

| segment_id | gold_role | pred_role | text |
|---|---|---|---|
| HELDOUT_S0016 | CLAIM | LIMITATION | Privacy review cannot be reduced to checkbox language even when a formal process exists. |

## Examples: Top Entity Errors

| segment_id | gold_entities | pred_entities | jaccard | text |
|---|---|---|---:|---|
| HELDOUT_S0004 | AI risk management; risk management | NIST AI RMF; AI risk management; risk management | 0.667 | NIST's profile document provides background for connecting AI risk management language to procurement and assurance workflows. |
| HELDOUT_S0005 | prompt injection; model behavior; controls | OWASP LLM Top 10; LLM application security; prompt injection; controls; model behavior | 0.600 | OWASP maintains a project hub where prompt injection, model behavior, and application controls are discussed together. |
| HELDOUT_S0006 | data protection; privacy | ICO AI guidance; data protection | 0.333 | The ICO guidance explains how data protection concepts frame AI design decisions before a system is deployed. |
| HELDOUT_S0007 | EU AI Act; high-risk AI; documentation | EU AI Act; high-risk AI; monitoring; documentation | 0.750 | The EU AI Act places high-risk systems within a regulatory setting that includes documentation, testing, and post-market duties. |
| HELDOUT_S0008 | route extraction; evaluation scripts; mismatch review; gold labels; benchmark | evaluation scripts; mismatch review; gold labels; benchmark; source context; RouteMap; evaluation | 0.500 | A route-extraction benchmark package contains source notes, gold labels, evaluation scripts, and mismatch review files. |
| HELDOUT_S0011 | monitoring | governance; monitoring | 0.500 | Monitoring is valuable, but it should be treated as an accountability signal rather than proof of safety. |
| HELDOUT_S0014 | secure AI development; retrieval; evaluation | secure AI development; controls; retrieval | 0.500 | Secure AI work is stronger when control evidence travels with retrieval results instead of living in a separate checklist. |
| HELDOUT_S0017 | retrieval; evaluation | retrieval | 0.500 | Route-based retrieval should help most when a question requires relation context rather than repeated keywords. |
| HELDOUT_S0020 | retrieval; evaluation | retrieval; RouteMap segment | 0.333 | Retrieval quality depends on whether relevant segments are connected, not merely present in the context window. |
| HELDOUT_S0021 | route provenance; source context | route provenance | 0.500 | Route provenance names the chain of sources, roles, and relations that support an answer. |

## Recommended Next Improvement Order

1. Improve semantic role coverage for held-out background, definition, result, and method wording without tuning directly to exact row strings.
2. Add a richer entity recognizer for held-out concepts such as `route provenance`, `retrieval trace`, `permission boundary`, and release-review terms.
3. Decouple relation prediction from role-only mapping so `supports_retrieval`, `maps_to`, and `requires` can be detected independently.
4. Tighten answer relevance for background/context rows so source-context passages do not become `YES` when role prediction is wrong.
5. Re-run this analysis after each change and keep a second held-out split untouched.
