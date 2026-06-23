# Strict Row Failure Audit: combined_v3 vs D_add_combined_answer

## Summary

| variant | role | entity_jaccard | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| combined | 0.532 | 0.506 | 0.595 | 0.443 | 0.848 | 0.051 | 0.253 | 0.354 | 0.443 |
| D | 0.595 | 0.506 | 0.658 | 0.430 | 0.848 | 0.025 | 0.304 | 0.304 | 0.316 |

## Win/Loss

| bucket | rows |
|---|---:|
| D better | 11 |
| combined_v3 better | 14 |
| both tie with at least one success | 13 |
| both tie wrong | 41 |

## Outcome Buckets

| outcome_bucket | rows |
|---|---:|
| both_strict_wrong | 29 |
| D_role_gain_but_other_fields_fail | 14 |
| combined_relaxed2_or_3_only | 12 |
| D_relaxed1_only | 11 |
| entity_blocks_D | 5 |
| answer_blocks_D | 4 |
| both_strict_correct | 2 |
| combined_strict_only | 2 |

## D Loses To Combined: Field Blockers

| blocker | rows |
|---|---:|
| role | 14 |
| entity | 0 |
| status | 8 |
| relation | 14 |
| answer | 0 |
| multiple_field | 14 |

## Combined Loses To D: Field Blockers

| blocker | rows |
|---|---:|
| role | 11 |
| entity | 0 |
| status | 10 |
| relation | 11 |
| answer | 0 |
| multiple_field | 11 |

## Top Rows To Inspect

| segment_id | gold_role | combined_role | D_role | combined_r1/r2/r3 | D_r1/r2/r3 | bucket | text |
|---|---|---|---|---|---|---|---|
| HELDOUT2_S0002 | BACKGROUND | BACKGROUND | BACKGROUND | NO/NO/NO | NO/NO/NO | answer_blocks_D | The release archive describes why model approval packets include evidence logs, reviewer notes, and unresolved caveats. |
| HELDOUT2_S0003 | BACKGROUND | BACKGROUND | BACKGROUND | NO/NO/NO | NO/NO/NO | answer_blocks_D | The privacy handbook gives consent examples before turning to any RouteMap annotation task. |
| HELDOUT2_S0004 | BACKGROUND | BACKGROUND | BACKGROUND | NO/NO/NO | NO/NO/NO | answer_blocks_D | A documentation page introduces retrieval trace diagrams for teams that have never used route labels. |
| HELDOUT2_S0006 | BACKGROUND | BACKGROUND | BACKGROUND | NO/NO/NO | NO/NO/NO | answer_blocks_D | The tool-use security note records common permission-check vocabulary used by incident responders. |
| HELDOUT2_S0007 | BACKGROUND | RESULT | BACKGROUND | NO/NO/NO | NO/NO/NO | D_role_gain_but_other_fields_fail | A benchmark design appendix lists source context, gold labels, and mismatch review artifacts for auditors. |
| HELDOUT2_S0008 | BACKGROUND | CLAIM | BACKGROUND | NO/NO/NO | NO/NO/NO | D_role_gain_but_other_fields_fail | The evidence selection primer explains how policy context can affect which passages are useful to reviewers. |
| HELDOUT2_S0009 | BACKGROUND | METHOD | BACKGROUND | NO/NO/NO | NO/NO/NO | D_role_gain_but_other_fields_fail | A model release governance catalog summarizes approval roles, audit trails, and release-board terminology. |
| HELDOUT2_S0010 | BACKGROUND | LIMITATION | BACKGROUND | NO/NO/NO | NO/NO/NO | D_role_gain_but_other_fields_fail | An incident response playbook provides background on escalation records without recommending a new classifier. |
| HELDOUT2_S0012 | CLAIM | METHOD | CLAIM | NO/NO/NO | NO/NO/NO | D_role_gain_but_other_fields_fail | Model release governance should treat missing evidence as a decision risk, not as harmless paperwork. |
| HELDOUT2_S0014 | CLAIM | CLAIM | CLAIM | NO/NO/NO | NO/NO/NO | entity_blocks_D | A retrieval trace matters because answer support depends on the path, not merely on a cited passage. |

## Interpretation

1. Ollama role gains land on some relaxed_1 rows: D has higher fine-role accuracy and converts rows where combined_v3 misses the exact fine role.
2. D beats combined_v3 on relaxed_1 because relaxed_1 requires exact fine role, answer correctness, and entity Jaccard >= 0.5; D keeps Ollama's stronger fine-role signal and borrows combined_v3 answer relevance plus ontology entities.
3. D loses on relaxed_2 and relaxed_3 because combined_v3's role errors often remain inside the correct coarse_4/coarse_3 buckets, while Ollama's wrong roles more often cross coarse boundaries.
4. Relation/status are strict-row blockers, but they are not relaxed-score blockers under the current definitions; strict still needs exact entities plus status and relation.
5. RouteMap v2 should test a modular extractor with Ollama-style fine-role routing, ontology entities, deterministic answer relevance, and a separate relation/status calibration layer evaluated with strict-row audits.
