# Held-Out Full Extraction Error Analysis

## Executive Summary

- Total rows: 80
- Role accuracy: 0.325
- Operative status accuracy: 0.500
- Relation accuracy: 0.312
- Answer relevance accuracy: 0.887
- Entity exact match: 0.013
- Entity average Jaccard: 0.284
- Strict full-row accuracy: 0.000
- Strict mismatch rows: 80

## Biggest Bottlenecks

- Role errors are the main upstream failure, especially overprediction of `CLAIM`.
- Relation and operative-status errors often cascade from wrong role predictions.
- Entity extraction has low exact match and many zero-overlap rows, showing that held-out entity wording is not covered by the current prediction heuristic.
- Answer relevance is comparatively strong but still fails for background rows predicted as answer-bearing roles.

## Role Confusion Matrix

| gold | pred | count |
|---|---|---:|
| BACKGROUND | BACKGROUND | 2 |
| BACKGROUND | CLAIM | 8 |
| CLAIM | CLAIM | 7 |
| CLAIM | LIMITATION | 2 |
| CLAIM | METHOD | 1 |
| DEFINE | CLAIM | 8 |
| DEFINE | DEFINE | 2 |
| EXAMPLE | CLAIM | 8 |
| EXAMPLE | EXAMPLE | 2 |
| LIMITATION | CLAIM | 3 |
| LIMITATION | LIMITATION | 5 |
| LIMITATION | METHOD | 1 |
| LIMITATION | NEXT_STEP | 1 |
| METHOD | CLAIM | 8 |
| METHOD | METHOD | 2 |
| NEXT_STEP | CLAIM | 4 |
| NEXT_STEP | LIMITATION | 1 |
| NEXT_STEP | METHOD | 1 |
| NEXT_STEP | NEXT_STEP | 4 |
| RESULT | CLAIM | 5 |
| RESULT | METHOD | 3 |
| RESULT | RESULT | 2 |

## Top Role Confusion Pairs

| gold_role | pred_role | count |
|---|---|---:|
| BACKGROUND | CLAIM | 8 |
| DEFINE | CLAIM | 8 |
| EXAMPLE | CLAIM | 8 |
| METHOD | CLAIM | 8 |
| RESULT | CLAIM | 5 |
| NEXT_STEP | CLAIM | 4 |
| LIMITATION | CLAIM | 3 |
| RESULT | METHOD | 3 |
| CLAIM | LIMITATION | 2 |
| CLAIM | METHOD | 1 |

## Relation Confusion Matrix

| gold | pred | count |
|---|---|---:|
| asserts | asserts | 7 |
| asserts | recommends | 1 |
| asserts | warns_about | 2 |
| defines | asserts | 8 |
| defines | defines | 2 |
| gives_example | asserts | 8 |
| gives_example | gives_example | 2 |
| limits | asserts | 1 |
| limits | limits | 1 |
| limits | recommends | 1 |
| maps_to | asserts | 1 |
| maps_to | recommends | 1 |
| proposes_next_test | asserts | 4 |
| proposes_next_test | proposes_next_test | 4 |
| proposes_next_test | recommends | 1 |
| proposes_next_test | warns_about | 1 |
| recommends | asserts | 6 |
| recommends | recommends | 1 |
| reports_usefulness | asserts | 3 |
| reports_usefulness | recommends | 2 |
| reports_usefulness | reports_usefulness | 2 |
| requires | asserts | 1 |
| sets_context | asserts | 8 |
| sets_context | sets_context | 2 |
| supports_retrieval | asserts | 2 |
| supports_retrieval | recommends | 1 |
| warns_about | asserts | 2 |
| warns_about | proposes_next_test | 1 |
| warns_about | warns_about | 4 |

## Operative Status Confusion Matrix

| gold | pred | count |
|---|---|---:|
| ACTIVE | ACTIVE | 27 |
| ACTIVE | LIMITED | 3 |
| DESCRIPTIVE | ACTIVE | 32 |
| DESCRIPTIVE | DESCRIPTIVE | 8 |
| LIMITED | ACTIVE | 3 |
| LIMITED | LIMITED | 4 |
| NEGATED | ACTIVE | 2 |
| NEGATED | NEGATED | 1 |

## Entity Diagnostics

- Rows with exact entity match: 1
- Rows with partial entity overlap: 62
- Rows with zero entity overlap: 17

### Most Common Missing Gold Entities

| entity | count |
|---|---:|
| evidence selection | 24 |
| route segment | 15 |
| model release governance | 14 |
| audit trail | 11 |
| answer support | 10 |
| tool-use security | 9 |
| consent boundary | 8 |
| source context | 8 |
| human review | 8 |
| policy context | 7 |

### Most Common Extra Predicted Entities

| entity | count |
|---|---:|
| routemap segment | 18 |
| retrieval | 17 |
| audit | 8 |
| governance | 5 |
| source context | 4 |
| evaluation | 3 |
| documentation | 2 |
| monitoring | 2 |
| privacy | 2 |
| release evidence | 1 |

## Strict Mismatch Clusters

| failure_pattern | count |
|---|---:|
| role+operative_status+relation+entity | 32 |
| entity | 24 |
| role+relation+entity | 14 |
| role+operative_status+relation+answer_relevant+entity | 7 |
| role+operative_status+relation+answer_relevant | 1 |
| answer_relevant+entity | 1 |
| relation+entity | 1 |

## Examples: Top Role Errors

| segment_id | gold_role | pred_role | text |
|---|---|---|---|
| HELDOUT2_S0001 | BACKGROUND | CLAIM | A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric exercise. |
| HELDOUT2_S0002 | BACKGROUND | CLAIM | The release archive describes why model approval packets include evidence logs, reviewer notes, and unresolved caveats. |
| HELDOUT2_S0003 | BACKGROUND | CLAIM | The privacy handbook gives consent examples before turning to any RouteMap annotation task. |
| HELDOUT2_S0005 | BACKGROUND | CLAIM | An agent memory briefing mentions risk, benchmark drift, and long-context failures while setting document scope. |
| HELDOUT2_S0006 | BACKGROUND | CLAIM | The tool-use security note records common permission-check vocabulary used by incident responders. |
| HELDOUT2_S0007 | BACKGROUND | CLAIM | A benchmark design appendix lists source context, gold labels, and mismatch review artifacts for auditors. |
| HELDOUT2_S0008 | BACKGROUND | CLAIM | The evidence selection primer explains how policy context can affect which passages are useful to reviewers. |
| HELDOUT2_S0009 | BACKGROUND | CLAIM | A model release governance catalog summarizes approval roles, audit trails, and release-board terminology. |
| HELDOUT2_S0013 | CLAIM | METHOD | Consent boundaries lose force when downstream permission checks are invisible to the answer composer. |
| HELDOUT2_S0017 | CLAIM | LIMITATION | Benchmark design is weaker when easy source context outnumbers adversarial route segments. |

## Examples: Top Entity Errors

| segment_id | gold_entities | pred_entities | jaccard | text |
|---|---|---|---:|---|
| HELDOUT2_S0001 | AI safety evaluation; policy context; risk management | governance; evaluation | 0.000 | A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric exercise. |
| HELDOUT2_S0002 | model release governance; evidence selection; human review; audit trail | human review | 0.250 | The release archive describes why model approval packets include evidence logs, reviewer notes, and unresolved caveats. |
| HELDOUT2_S0003 | privacy; consent boundary; RouteMap | privacy; RouteMap | 0.667 | The privacy handbook gives consent examples before turning to any RouteMap annotation task. |
| HELDOUT2_S0004 | retrieval trace; route segment; RouteMap | retrieval trace; retrieval; RouteMap segment; documentation | 0.167 | A documentation page introduces retrieval trace diagrams for teams that have never used route labels. |
| HELDOUT2_S0005 | agent memory; benchmark; risk management; source context | benchmark; agent memory | 0.500 | An agent memory briefing mentions risk, benchmark drift, and long-context failures while setting document scope. |
| HELDOUT2_S0006 | tool-use security; permission boundary; incident response | permission boundary | 0.333 | The tool-use security note records common permission-check vocabulary used by incident responders. |
| HELDOUT2_S0008 | evidence selection; policy context; human review | human review; retrieval; source context; RouteMap segment | 0.167 | The evidence selection primer explains how policy context can affect which passages are useful to reviewers. |
| HELDOUT2_S0009 | model release governance; audit trail; human review | governance; audit | 0.000 | A model release governance catalog summarizes approval roles, audit trails, and release-board terminology. |
| HELDOUT2_S0010 | incident response; source context; human review | monitoring; incident response | 0.250 | An incident response playbook provides background on escalation records without recommending a new classifier. |
| HELDOUT2_S0011 | AI safety evaluation; evaluation; audit trail | evaluation | 0.333 | AI safety evaluation becomes more credible when disagreement remains traceable instead of hidden behind an average. |

## Recommended Next Improvement Order

1. Improve semantic role coverage for held-out background, definition, result, and method wording without tuning directly to exact row strings.
2. Add a richer entity recognizer for held-out concepts such as `route provenance`, `retrieval trace`, `permission boundary`, and release-review terms.
3. Decouple relation prediction from role-only mapping so `supports_retrieval`, `maps_to`, and `requires` can be detected independently.
4. Tighten answer relevance for background/context rows so source-context passages do not become `YES` when role prediction is wrong.
5. Re-run this analysis after each change and keep a second held-out split untouched.
