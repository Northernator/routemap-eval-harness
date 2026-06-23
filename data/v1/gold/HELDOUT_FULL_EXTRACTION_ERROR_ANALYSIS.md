# Held-Out Full Extraction Error Analysis

## Executive Summary

- Total rows: 80
- Role accuracy: 0.450
- Operative status accuracy: 0.613
- Relation accuracy: 0.438
- Answer relevance accuracy: 0.875
- Entity exact match: 0.300
- Entity average Jaccard: 0.405
- Strict full-row accuracy: 0.113
- Strict mismatch rows: 71

## Biggest Bottlenecks

- Role errors are the main upstream failure, especially overprediction of `CLAIM`.
- Relation and operative-status errors often cascade from wrong role predictions.
- Entity extraction has low exact match and many zero-overlap rows, showing that held-out entity wording is not covered by the current prediction heuristic.
- Answer relevance is comparatively strong but still fails for background rows predicted as answer-bearing roles.

## Role Confusion Matrix

| gold | pred | count |
|---|---|---:|
| BACKGROUND | BACKGROUND | 4 |
| BACKGROUND | CLAIM | 5 |
| BACKGROUND | METHOD | 1 |
| CLAIM | CLAIM | 10 |
| DEFINE | CLAIM | 8 |
| DEFINE | DEFINE | 2 |
| EXAMPLE | CLAIM | 3 |
| EXAMPLE | EXAMPLE | 7 |
| LIMITATION | CLAIM | 6 |
| LIMITATION | LIMITATION | 4 |
| METHOD | CLAIM | 7 |
| METHOD | METHOD | 3 |
| NEXT_STEP | CLAIM | 5 |
| NEXT_STEP | NEXT_STEP | 5 |
| RESULT | CLAIM | 9 |
| RESULT | RESULT | 1 |

## Top Role Confusion Pairs

| gold_role | pred_role | count |
|---|---|---:|
| RESULT | CLAIM | 9 |
| DEFINE | CLAIM | 8 |
| METHOD | CLAIM | 7 |
| LIMITATION | CLAIM | 6 |
| BACKGROUND | CLAIM | 5 |
| NEXT_STEP | CLAIM | 5 |
| EXAMPLE | CLAIM | 3 |
| BACKGROUND | METHOD | 1 |

## Relation Confusion Matrix

| gold | pred | count |
|---|---|---:|
| asserts | asserts | 10 |
| defines | asserts | 8 |
| defines | defines | 2 |
| gives_example | asserts | 3 |
| gives_example | gives_example | 7 |
| limits | asserts | 2 |
| limits | limits | 3 |
| maps_to | asserts | 4 |
| maps_to | recommends | 1 |
| proposes_next_test | asserts | 5 |
| proposes_next_test | proposes_next_test | 5 |
| recommends | asserts | 3 |
| recommends | recommends | 2 |
| reports_usefulness | asserts | 6 |
| sets_context | asserts | 5 |
| sets_context | recommends | 1 |
| sets_context | sets_context | 4 |
| supports_retrieval | asserts | 3 |
| supports_retrieval | supports_retrieval | 1 |
| warns_about | asserts | 4 |
| warns_about | warns_about | 1 |

## Operative Status Confusion Matrix

| gold | pred | count |
|---|---|---:|
| ACTIVE | ACTIVE | 29 |
| DESCRIPTIVE | ACTIVE | 26 |
| DESCRIPTIVE | DESCRIPTIVE | 14 |
| LIMITED | ACTIVE | 4 |
| LIMITED | LIMITED | 1 |
| NEGATED | ACTIVE | 1 |
| NEGATED | NEGATED | 5 |

## Entity Diagnostics

- Rows with exact entity match: 24
- Rows with partial entity overlap: 23
- Rows with zero entity overlap: 33

### Most Common Missing Gold Entities

| entity | count |
|---|---:|
| evaluation | 16 |
| source context | 9 |
| privacy | 9 |
| human review | 7 |
| permission boundary | 6 |
| routemap segment | 5 |
| controls | 4 |
| secure ai development | 2 |
| llm application security | 2 |
| ai risk management | 2 |

### Most Common Extra Predicted Entities

| entity | count |
|---|---:|
| model behavior | 13 |
| routemap segment | 11 |
| ai risk | 9 |
| data protection | 8 |
| data | 4 |
| routemap | 4 |
| nist ai rmf | 1 |
| owasp llm top 10 | 1 |
| ico ai guidance | 1 |
| long-context systems | 1 |

## Strict Mismatch Clusters

| failure_pattern | count |
|---|---:|
| entity | 22 |
| role+operative_status+relation+entity | 14 |
| role+operative_status+relation | 11 |
| none | 9 |
| role+relation+entity | 9 |
| role+operative_status+relation+answer_relevant+entity | 6 |
| answer_relevant+entity | 4 |
| role+relation | 4 |
| relation+entity | 1 |

## Examples: Top Role Errors

| segment_id | gold_role | pred_role | text |
|---|---|---|---|
| HELDOUT_S0001 | BACKGROUND | CLAIM | The OECD AI principles page gives policy context for trustworthy AI and names common public-interest concerns. |
| HELDOUT_S0002 | BACKGROUND | CLAIM | A vendor white paper describes the setting for secure model release reviews and explains why release evidence is collected. |
| HELDOUT_S0004 | BACKGROUND | METHOD | NIST's profile document provides background for connecting AI risk management language to procurement and assurance workflows. |
| HELDOUT_S0008 | BACKGROUND | CLAIM | A route-extraction benchmark package contains source notes, gold labels, evaluation scripts, and mismatch review files. |
| HELDOUT_S0009 | BACKGROUND | CLAIM | The project README records why long-context memory needs both raw source access and compact route pointers. |
| HELDOUT_S0010 | BACKGROUND | CLAIM | A CISA briefing introduces AI roadmap language for critical infrastructure and cyber defence audiences. |
| HELDOUT_S0021 | DEFINE | CLAIM | Route provenance names the chain of sources, roles, and relations that support an answer. |
| HELDOUT_S0022 | DEFINE | CLAIM | A retrieval trace is the ordered path from query intent to selected evidence and final answer support. |
| HELDOUT_S0023 | DEFINE | CLAIM | AI risk posture denotes the current exposure created by model capability, deployment context, controls, and oversight. |
| HELDOUT_S0024 | DEFINE | CLAIM | A consent boundary describes where a user permission applies, expires, or must be renewed. |

## Examples: Top Entity Errors

| segment_id | gold_entities | pred_entities | jaccard | text |
|---|---|---|---:|---|
| HELDOUT_S0001 | AI principles; trustworthy AI; source context | AI risk | 0.000 | The OECD AI principles page gives policy context for trustworthy AI and names common public-interest concerns. |
| HELDOUT_S0002 | model release review; release evidence; secure AI development | model behavior | 0.000 | A vendor white paper describes the setting for secure model release reviews and explains why release evidence is collected. |
| HELDOUT_S0003 | LLM application security; source context | RouteMap segment | 0.000 | This source summarizes common LLM application security issues for readers who need document-level context before annotation. |
| HELDOUT_S0004 | AI risk management; risk management | NIST AI RMF; risk management; AI risk | 0.250 | NIST's profile document provides background for connecting AI risk management language to procurement and assurance workflows. |
| HELDOUT_S0005 | prompt injection; model behavior; controls | OWASP LLM Top 10; prompt injection; model behavior | 0.500 | OWASP maintains a project hub where prompt injection, model behavior, and application controls are discussed together. |
| HELDOUT_S0006 | data protection; privacy | ICO AI guidance; data protection; data | 0.250 | The ICO guidance explains how data protection concepts frame AI design decisions before a system is deployed. |
| HELDOUT_S0007 | EU AI Act; high-risk AI; documentation | EU AI Act; AI risk | 0.250 | The EU AI Act places high-risk systems within a regulatory setting that includes documentation, testing, and post-market duties. |
| HELDOUT_S0008 | route extraction; evaluation scripts; mismatch review; gold labels; benchmark | benchmark | 0.200 | A route-extraction benchmark package contains source notes, gold labels, evaluation scripts, and mismatch review files. |
| HELDOUT_S0009 | long-context memory; source context; agent memory | agent memory; long-context systems | 0.250 | The project README records why long-context memory needs both raw source access and compact route pointers. |
| HELDOUT_S0010 | AI roadmap | CISA AI roadmap; AI roadmap | 0.500 | A CISA briefing introduces AI roadmap language for critical infrastructure and cyber defence audiences. |

## Recommended Next Improvement Order

1. Improve semantic role coverage for held-out background, definition, result, and method wording without tuning directly to exact row strings.
2. Add a richer entity recognizer for held-out concepts such as `route provenance`, `retrieval trace`, `permission boundary`, and release-review terms.
3. Decouple relation prediction from role-only mapping so `supports_retrieval`, `maps_to`, and `requires` can be detected independently.
4. Tighten answer relevance for background/context rows so source-context passages do not become `YES` when role prediction is wrong.
5. Re-run this analysis after each change and keep a second held-out split untouched.
