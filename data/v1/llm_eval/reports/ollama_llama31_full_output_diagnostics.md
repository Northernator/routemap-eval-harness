# Ollama llama3.1 Full Output Diagnostics

## Executive Summary

- Total predictions: 79
- Total raw output records: 158
- Empty predicted entity rows: 79
- Average predicted entities per row: 0.000
- Average gold entities per row: 3.051
- Likely role collapse: top 1 role(s) cover 1.000 of predictions.
- Likely failure cause: Provider calls appear to have failed before semantic extraction: raw_response values contain connection-refused error JSON, then ingestion normalized missing extraction fields into default BACKGROUND/DESCRIPTIVE/sets_context/MAYBE with empty entities.

## Output-Level Diagnostics

| metric | value |
|---|---:|
| total outputs | 79 |
| extraction object count | 0 |
| raw_response count | 79 |
| raw_response error JSON count | 79 |
| average raw response length | 120.0 |

## Role Diagnostics

### Gold Role Counts

| role | count |
|---|---:|
| BACKGROUND | 10 |
| CLAIM | 10 |
| DEFINE | 10 |
| METHOD | 10 |
| RESULT | 10 |
| LIMITATION | 10 |
| EXAMPLE | 10 |
| NEXT_STEP | 9 |

### Predicted Role Counts

| role | count |
|---|---:|
| BACKGROUND | 79 |

### Role Confusion Matrix

| gold \ pred | BACKGROUND |
|---|---:|
| BACKGROUND | 10 |
| CLAIM | 10 |
| DEFINE | 10 |
| EXAMPLE | 10 |
| LIMITATION | 10 |
| METHOD | 10 |
| NEXT_STEP | 9 |
| RESULT | 10 |

### Top Role Confusions

| gold | pred | count |
|---|---|---:|
| CLAIM | BACKGROUND | 10 |
| DEFINE | BACKGROUND | 10 |
| METHOD | BACKGROUND | 10 |
| RESULT | BACKGROUND | 10 |
| LIMITATION | BACKGROUND | 10 |
| EXAMPLE | BACKGROUND | 10 |
| NEXT_STEP | BACKGROUND | 9 |

## Entity Diagnostics

| metric | value |
|---|---:|
| rows with empty pred_entities | 79 |
| average predicted entities per row | 0.000 |
| average gold entities per row | 3.051 |
| gold non-empty but pred empty | 79 |
| pred non-empty zero overlap | 0 |
| eval zero-overlap rows | 79 |
| non-canonical predicted strings | 0 |

### Top Predicted Entity Strings

| entity | count |
|---|---:|

### Top Gold Entity Strings

| entity | count |
|---|---:|
| evidence selection | 23 |
| human review | 21 |
| answer support | 16 |
| RouteMap segment | 15 |
| permission boundary | 15 |
| model release governance | 14 |
| source context | 13 |
| audit trail | 11 |
| retrieval trace | 11 |
| benchmark | 11 |
| agent memory | 10 |
| privacy | 9 |
| tool-use security | 9 |
| consent boundary | 8 |
| policy context | 7 |

## Status Diagnostics

| gold \ pred | DESCRIPTIVE |
|---|---:|
| ACTIVE | 29 |
| DESCRIPTIVE | 40 |
| LIMITED | 7 |
| NEGATED | 3 |

## Relation Diagnostics

| gold \ pred | sets_context |
|---|---:|
| asserts | 10 |
| defines | 10 |
| gives_example | 10 |
| limits | 3 |
| maps_to | 2 |
| proposes_next_test | 9 |
| recommends | 7 |
| reports_usefulness | 7 |
| requires | 1 |
| sets_context | 10 |
| supports_retrieval | 3 |
| warns_about | 7 |

## Answer Relevance Diagnostics

| gold \ pred | MAYBE |
|---|---:|
| MAYBE | 3 |
| NO | 7 |
| YES | 69 |

## 10 Worst Examples

| segment_id | gold_role | pred_role | entity_j | failure | preview |
|---|---|---|---:|---|---|
| HELDOUT2_S0011 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | AI safety evaluation becomes more credible when disagreement remains traceable instead of hidden behind an average. |
| HELDOUT2_S0012 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | Model release governance should treat missing evidence as a decision risk, not as harmless paperwork. |
| HELDOUT2_S0013 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | Consent boundaries lose force when downstream permission checks are invisible to the answer composer. |
| HELDOUT2_S0014 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | A retrieval trace matters because answer support depends on the path, not merely on a cited passage. |
| HELDOUT2_S0015 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | Agent memory can amplify stale assumptions when route provenance is absent from recall. |
| HELDOUT2_S0016 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | Controls that never travel with retrieved evidence rarely change practical review behaviour. |
| HELDOUT2_S0017 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | Benchmark design is weaker when easy source context outnumbers adversarial route segments. |
| HELDOUT2_S0018 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | Human review adds value only if reviewers can inspect the evidence selection path. |
| HELDOUT2_S0019 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | Tool-use security depends on permission boundaries being checked at the moment of action. |
| HELDOUT2_S0020 | CLAIM | BACKGROUND | 0.000 | role+entity+status+relation+answer | An audit trail without answer support is evidence of activity rather than evidence of reliability. |

## 10 Examples Where Role Was Correct But Entities Failed

| segment_id | role | gold_entities | pred_entities |
|---|---|---|---|
| HELDOUT2_S0001 | BACKGROUND | AI safety evaluation; policy context; risk management |  |
| HELDOUT2_S0002 | BACKGROUND | model release governance; evidence selection; human review; audit trail |  |
| HELDOUT2_S0003 | BACKGROUND | privacy; consent boundary; RouteMap |  |
| HELDOUT2_S0004 | BACKGROUND | retrieval trace; route segment; RouteMap |  |
| HELDOUT2_S0005 | BACKGROUND | agent memory; benchmark; risk management; source context |  |
| HELDOUT2_S0006 | BACKGROUND | tool-use security; permission boundary; incident response |  |
| HELDOUT2_S0007 | BACKGROUND | benchmark; source context; gold labels; mismatch review |  |
| HELDOUT2_S0008 | BACKGROUND | evidence selection; policy context; human review |  |
| HELDOUT2_S0009 | BACKGROUND | model release governance; audit trail; human review |  |
| HELDOUT2_S0010 | BACKGROUND | incident response; source context; human review |  |

## 10 Examples Where Entities Were Empty

| segment_id | gold_entities | raw_or_rationale_preview |
|---|---|---|
| HELDOUT2_S0001 | AI safety evaluation; policy context; risk management | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |
| HELDOUT2_S0002 | model release governance; evidence selection; human review; audit trail | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |
| HELDOUT2_S0003 | privacy; consent boundary; RouteMap | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |
| HELDOUT2_S0004 | retrieval trace; route segment; RouteMap | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |
| HELDOUT2_S0005 | agent memory; benchmark; risk management; source context | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |
| HELDOUT2_S0006 | tool-use security; permission boundary; incident response | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |
| HELDOUT2_S0007 | benchmark; source context; gold labels; mismatch review | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |
| HELDOUT2_S0008 | evidence selection; policy context; human review | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |
| HELDOUT2_S0009 | model release governance; audit trail; human review | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |
| HELDOUT2_S0010 | incident response; source context; human review | {"error": "<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"} |

## Recommendation For Prompt V2

Do not change the prompt yet if the saved run consists of connection-refused raw responses. First rerun only after confirming Ollama is reachable and the runner records actual model text. Then validate whether raw model JSON contains canonical entity labels. If actual model text still omits entities, prompt v2 should require at least 1-5 canonical entities selected from the ontology when supported by passage text, and should include a negative instruction not to return an empty entity list unless no ontology concept is present.