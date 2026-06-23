# Entity Error Analysis on Fresh Adjudicated Test

## Row Categories

| category | rows |
|---|---:|
| ontology_v1_wins | 49 |
| tie | 16 |
| current_extractor_wins | 9 |
| both_zero_overlap | 5 |

## Zero-Overlap Rows

| segment_id | current_zero | ontology_zero | gold | current | ontology_v1 |
|---|---|---|---|---|---|
| HELDOUT2_S0001 | YES | NO | AI safety evaluation; policy context; risk management | evaluation; governance | AI safety evaluation; evaluation; governance; policy context; risk management |
| HELDOUT2_S0009 | YES | NO | audit trail; human review; model release governance | governance; audit | audit trail; governance; model release governance |
| HELDOUT2_S0012 | YES | NO | evidence selection; model release governance; risk management | governance | governance; model release governance |
| HELDOUT2_S0030 | YES | NO | controls; evidence selection; human review | RouteMap segment | human review |
| HELDOUT2_S0034 | YES | YES | agent memory; route provenance; source context | RouteMap segment |  |
| HELDOUT2_S0052 | YES | YES | AI safety evaluation; model release governance; risk management | RouteMap segment |  |
| HELDOUT2_S0054 | YES | NO | answer support; retrieval trace; RouteMap segment | retrieval | retrieval; retrieval trace |
| HELDOUT2_S0061 | YES | YES | benchmark; incident response; model release governance | monitoring | evaluation; governance |
| HELDOUT2_S0066 | YES | NO | agent memory; permission boundary; tool-use security | RouteMap segment | LLM application security; tool-use security |
| HELDOUT2_S0074 | YES | YES | agent memory; route provenance; source context | RouteMap segment |  |
| HELDOUT2_S0077 | YES | YES | agent memory; incident response; retrieval trace | retrieval | retrieval |
| HELDOUT2_S0079 | YES | NO | audit trail; evidence selection; model release governance | human review; retrieval | evidence selection; human review |

## Rows Where Current Extractor Wins

| segment_id | current J | ontology J | gold |
|---|---:|---:|---|
| HELDOUT2_S0007 | 1.000 | 0.800 | benchmark; gold labels; mismatch review; source context |
| HELDOUT2_S0014 | 0.400 | 0.333 | answer support; evidence selection; retrieval trace |
| HELDOUT2_S0017 | 1.000 | 0.750 | benchmark; RouteMap segment; source context |
| HELDOUT2_S0031 | 0.250 | 0.200 | answer support; human review; retrieval trace |
| HELDOUT2_S0035 | 0.667 | 0.500 | permission boundary; RouteMap segment; tool-use security |
| HELDOUT2_S0040 | 0.333 | 0.250 | evidence selection; human review; RouteMap segment |
| HELDOUT2_S0060 | 0.667 | 0.500 | answer support; evidence selection; RouteMap segment |
| HELDOUT2_S0075 | 0.333 | 0.250 | answer support; evidence selection; privacy |
| HELDOUT2_S0076 | 0.333 | 0.250 | permission boundary; RouteMap segment; tool-use security |

## Rows Where Ontology V1 Wins

| segment_id | current J | ontology J | gold |
|---|---:|---:|---|
| HELDOUT2_S0001 | 0.000 | 0.600 | AI safety evaluation; policy context; risk management |
| HELDOUT2_S0002 | 0.250 | 0.750 | audit trail; evidence selection; human review; model release governance |
| HELDOUT2_S0003 | 0.667 | 1.000 | consent boundary; privacy; RouteMap |
| HELDOUT2_S0004 | 0.400 | 0.750 | retrieval trace; RouteMap; RouteMap segment |
| HELDOUT2_S0005 | 0.500 | 0.750 | agent memory; benchmark; risk management; source context |
| HELDOUT2_S0006 | 0.333 | 0.750 | incident response; permission boundary; tool-use security |
| HELDOUT2_S0008 | 0.167 | 0.600 | evidence selection; human review; policy context |
| HELDOUT2_S0009 | 0.000 | 0.500 | audit trail; human review; model release governance |
| HELDOUT2_S0010 | 0.250 | 0.333 | human review; incident response; source context |
| HELDOUT2_S0011 | 0.333 | 1.000 | AI safety evaluation; audit trail; evaluation |
| HELDOUT2_S0012 | 0.000 | 0.250 | evidence selection; model release governance; risk management |
| HELDOUT2_S0013 | 0.250 | 0.667 | answer support; consent boundary; permission boundary |
| HELDOUT2_S0015 | 0.500 | 0.667 | agent memory; route provenance; source context |
| HELDOUT2_S0018 | 0.250 | 0.667 | evidence selection; human review; retrieval trace |
| HELDOUT2_S0019 | 0.333 | 0.500 | controls; permission boundary; tool-use security |
| HELDOUT2_S0020 | 0.250 | 0.667 | answer support; audit trail; evaluation |
| HELDOUT2_S0021 | 0.750 | 1.000 | answer support; evidence selection; route provenance; source context |
| HELDOUT2_S0022 | 0.250 | 0.500 | answer support; evidence selection; retrieval trace |
| HELDOUT2_S0024 | 0.250 | 0.500 | evaluation; model release governance; risk management |
| HELDOUT2_S0026 | 0.250 | 0.500 | route extraction; RouteMap; RouteMap segment |
| HELDOUT2_S0028 | 0.200 | 0.500 | audit trail; human review; model release governance |
| HELDOUT2_S0030 | 0.000 | 0.333 | controls; evidence selection; human review |
| HELDOUT2_S0032 | 0.250 | 0.333 | evidence selection; human review; model release governance |
| HELDOUT2_S0033 | 0.250 | 0.500 | consent boundary; evidence selection; permission boundary |
| HELDOUT2_S0036 | 0.250 | 0.500 | controls; incident response; retrieval trace |
| HELDOUT2_S0037 | 0.250 | 0.667 | benchmark; policy context; RouteMap segment |
| HELDOUT2_S0038 | 0.250 | 0.667 | answer support; evidence selection; human review |
| HELDOUT2_S0039 | 0.500 | 1.000 | answer support; audit trail; human review |
| HELDOUT2_S0041 | 0.500 | 0.600 | answer support; evaluation; route provenance |
| HELDOUT2_S0043 | 0.667 | 1.000 | consent boundary; permission boundary; privacy |
| HELDOUT2_S0045 | 0.250 | 0.400 | human review; permission boundary; tool-use security |
| HELDOUT2_S0048 | 0.250 | 0.667 | answer support; audit trail; model release governance |
| HELDOUT2_S0049 | 0.500 | 0.750 | evidence selection; RouteMap segment; source context |
| HELDOUT2_S0050 | 0.333 | 0.667 | mismatch review; policy context; claims |
| HELDOUT2_S0051 | 0.333 | 0.667 | benchmark; evaluation; policy context |
| HELDOUT2_S0054 | 0.000 | 0.250 | answer support; retrieval trace; RouteMap segment |
| HELDOUT2_S0057 | 0.250 | 0.667 | audit trail; evidence selection; human review |
| HELDOUT2_S0058 | 0.250 | 0.333 | benchmark; incident response; RouteMap segment |
| HELDOUT2_S0059 | 0.250 | 0.667 | controls; policy context; risk management |
| HELDOUT2_S0062 | 0.250 | 0.500 | evaluation; model release governance; source context |
| HELDOUT2_S0063 | 0.667 | 1.000 | consent boundary; permission boundary; privacy |
| HELDOUT2_S0065 | 0.333 | 0.667 | agent memory; benchmark; evidence selection |
| HELDOUT2_S0066 | 0.000 | 0.250 | agent memory; permission boundary; tool-use security |
| HELDOUT2_S0069 | 0.250 | 0.667 | audit trail; human review; model release governance |
| HELDOUT2_S0070 | 0.333 | 0.500 | answer support; evidence selection; RouteMap segment |
| HELDOUT2_S0071 | 0.250 | 0.500 | AI safety evaluation; consent boundary; privacy |
| HELDOUT2_S0072 | 0.250 | 0.500 | audit trail; human review; model release governance |
| HELDOUT2_S0079 | 0.000 | 0.250 | audit trail; evidence selection; model release governance |
| HELDOUT2_S0080 | 0.250 | 0.500 | answer support; policy context; RouteMap segment |

## Ontology V1 Missing Entities

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
| tool-use security | 4 |
| agent memory | 4 |
| incident response | 4 |
| route extraction | 3 |
| route provenance | 3 |
| audit trail | 2 |
| controls | 2 |
| evaluation | 2 |
| claims | 1 |
| policy context | 1 |

## Ontology V1 Extra Entities

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

## Recommended Ontology Additions

| entity | missing count | recommendation |
|---|---:|---|
| evidence selection | 15 | Add or broaden triggers for `evidence selection` using fresh error rows before any future non-test tuning. |
| model release governance | 9 | Add or broaden triggers for `model release governance` using fresh error rows before any future non-test tuning. |
| human review | 7 | Add or broaden triggers for `human review` using fresh error rows before any future non-test tuning. |
| source context | 7 | Add or broaden triggers for `source context` using fresh error rows before any future non-test tuning. |
| answer support | 7 | Add or broaden triggers for `answer support` using fresh error rows before any future non-test tuning. |
| RouteMap segment | 6 | Add or broaden triggers for `RouteMap segment` using fresh error rows before any future non-test tuning. |
| risk management | 5 | Add or broaden triggers for `risk management` using fresh error rows before any future non-test tuning. |
| retrieval trace | 4 | Add or broaden triggers for `retrieval trace` using fresh error rows before any future non-test tuning. |
| privacy | 4 | Add or broaden triggers for `privacy` using fresh error rows before any future non-test tuning. |
| permission boundary | 4 | Add or broaden triggers for `permission boundary` using fresh error rows before any future non-test tuning. |
| tool-use security | 4 | Add or broaden triggers for `tool-use security` using fresh error rows before any future non-test tuning. |
| agent memory | 4 | Add or broaden triggers for `agent memory` using fresh error rows before any future non-test tuning. |