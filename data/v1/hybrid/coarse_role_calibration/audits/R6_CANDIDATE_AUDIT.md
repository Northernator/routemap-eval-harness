# R6 Candidate Row-Level Audit

## Executive Summary

R6_coarse3_guard_combined_status_relation is the best current RouteMap v2 candidate in this calibration set because it keeps combined_v3 strict and relaxed_3 performance, beats combined_v3 on relaxed_1 and relaxed_2, and repairs fine-role accuracy with a coarse_3 guard over the D/Ollama role layer.

The row-level audit supports the claim: R6 has the strongest role accuracy and the best relaxed_1/relaxed_2 scores, while preserving combined_v3 relation/status calibration enough to tie the best strict score. There is no row-level evidence that the gain is only a metric artefact: the improvements concentrate in explainable role repairs and coarse-boundary saves, not hidden gold-driven prediction edits.

Strict full-row extraction remains blocked mainly by exact entity recovery. R6 often has the right role and enough entity overlap for relaxed metrics, but strict requires exact entity sets plus status, relation, and answer correctness.

## Metrics

| variant | role | coarse_5 | coarse_4 | coarse_3 | entity Jaccard | entity exact | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| combined_v3 | 0.532 | 0.620 | 0.696 | 0.823 | 0.506 | 0.076 | 0.595 | 0.443 | 0.848 | 0.051 | 0.253 | 0.354 | 0.443 |
| D_add_combined_answer | 0.595 | 0.595 | 0.595 | 0.608 | 0.506 | 0.076 | 0.658 | 0.430 | 0.848 | 0.025 | 0.304 | 0.304 | 0.316 |
| R6 | 0.709 | 0.734 | 0.772 | 0.823 | 0.506 | 0.076 | 0.595 | 0.443 | 0.848 | 0.051 | 0.354 | 0.392 | 0.443 |

## Win/Loss/Tie Table

| bucket | rows |
|---|---|
| R6 beats both combined_v3 and D | 0 |
| R6 beats D but ties combined_v3 | 13 |
| R6 beats combined_v3 but ties D | 8 |
| combined_v3 beats R6 | 1 |
| D beats R6 | 3 |
| all three fail | 41 |
| all three succeed | 2 |
| all three tie with partial success | 11 |

## Outcome Buckets

| outcome_bucket | rows |
|---|---|
| multi_field_blocks_R6 | 26 |
| R6_preserves_combined_relaxed3 | 13 |
| R6_role_repair_success | 13 |
| entity_blocks_R6 | 11 |
| R6_role_repair_failure | 11 |
| all_strict_correct | 2 |
| R6_coarse_guard_saved_row | 2 |
| answer_blocks_R6 | 1 |

## Role Repair Analysis

| measure | rows |
|---|---|
| coarse_3_guard_changed_D_role | 40 |
| changes_helped | 13 |
| changes_hurt | 3 |
| changes_improved_fine_role | 20 |
| changes_improved_coarse3_only | 8 |
| R6_fine_role_correct_but_strict_fails | 52 |

## Strict Blocker Analysis for R6

| blocker | rows |
|---|---|
| entity | 73 |
| relation | 44 |
| status | 32 |
| answer | 12 |
| role | 23 |
| multiple | 47 |

## Manual Inspection List

| segment_id | reason | gold_role | combined_role | D_role | R6_role | R6 blockers | text |
|---|---|---|---|---|---|---|---|
| HELDOUT2_S0015 | R6 improved relaxed score but not strict | CLAIM | CLAIM | LIMITATION | CLAIM | entity | Agent memory can amplify stale assumptions when route provenance is absent from recall. |
| HELDOUT2_S0019 | R6 improved relaxed score but not strict | CLAIM | EXAMPLE | CLAIM | CLAIM | entity; status; relation; multiple | Tool-use security depends on permission boundaries being checked at the moment of action. |
| HELDOUT2_S0020 | R6 improved relaxed score but not strict | CLAIM | DEFINE | CLAIM | CLAIM | entity; status; relation; multiple | An audit trail without answer support is evidence of activity rather than evidence of reliability. |
| HELDOUT2_S0001 | R6 role correct but entity/relation blocks strict | BACKGROUND | BACKGROUND | BACKGROUND | BACKGROUND | entity | A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric exercise. |
| HELDOUT2_S0002 | R6 role correct but entity/relation blocks strict | BACKGROUND | BACKGROUND | BACKGROUND | BACKGROUND | entity; answer; multiple | The release archive describes why model approval packets include evidence logs, reviewer notes, and unresolved caveats. |
| HELDOUT2_S0004 | R6 role correct but entity/relation blocks strict | BACKGROUND | BACKGROUND | BACKGROUND | BACKGROUND | entity; answer; multiple | A documentation page introduces retrieval trace diagrams for teams that have never used route labels. |
| HELDOUT2_S0080 | R6 loses to combined_v3 | EXAMPLE | METHOD | RESULT | RESULT | role; entity; status; relation; multiple | A final answer that cites policy context but omits the controlling route segment shows a support failure. |
| HELDOUT2_S0056 | coarse_3 guard changed role and hurt | LIMITATION | METHOD | LIMITATION | METHOD | role; entity; status; relation; multiple | Permission checks are not enough when the tool output can leak private data through a later route. |
| HELDOUT2_S0057 | coarse_3 guard changed role and hurt | LIMITATION | METHOD | LIMITATION | METHOD | role; entity; status; relation; multiple | Human review is constrained when audit trails omit rejected evidence and reviewer rationale. |
| HELDOUT2_S0059 | coarse_3 guard changed role and hurt | LIMITATION | DEFINE | LIMITATION | DEFINE | role; entity; status; relation; multiple | Policy context can warn about risk without specifying the control step needed for a particular system. |
| HELDOUT2_S0022 | R6 improved relaxed score but not strict | DEFINE | CLAIM | BACKGROUND | CLAIM | role; entity; status; relation; multiple | Retrieval trace names the visible sequence from question intent through evidence selection to final response. |
| HELDOUT2_S0026 | R6 improved relaxed score but not strict | DEFINE | METHOD | BACKGROUND | METHOD | role; entity; status; relation; multiple | A route segment label marks the job a passage performs inside a larger retrieval chain. |
| HELDOUT2_S0028 | R6 improved relaxed score but not strict | DEFINE | CLAIM | DEFINE | DEFINE | entity; status; relation; multiple | Audit trail, in this setting, names records that let reviewers reconstruct a release or retrieval decision. |
| HELDOUT2_S0033 | R6 improved relaxed score but not strict | METHOD | METHOD | BACKGROUND | METHOD | entity; relation; multiple | Map consent records to permission checks before selecting evidence for a privacy-sensitive answer. |
| HELDOUT2_S0035 | R6 improved relaxed score but not strict | METHOD | METHOD | BACKGROUND | METHOD | entity; relation; multiple | Log tool calls with permission scope, selected route segment, and the reason the action was allowed. |

## Final Recommendation

1. Promote R6 as the current modular RouteMap v2 candidate for the next validation step, not as a final extractor.
2. Remaining bottleneck is exact entity recovery; relation is secondary, while status and answer are smaller blockers in this audit.
3. Next work should be holdout validation with an entity-exact recovery ablation queued immediately after it. R6 is calibrated on this set, so promotion needs a fresh holdout before architecture lock-in.
4. Next exact test: run R6 on a fresh heldout split or frozen blind sample, then compare R6 against combined_v3 and D with the same row-level audit. If holdout holds, run an entity canonicalization/over-generation pruning ablation with strict-blocker deltas.

## Provenance

- combined_v3: `data\v1\gold\heldout_full_extraction_pred_combined_v3_fresh.csv`
- D baseline: `data\v1\hybrid\field_ablation\predictions\D_add_combined_answer_predictions.csv`
- R6: `data\v1\hybrid\coarse_role_calibration\predictions\R6_coarse3_guard_combined_status_relation_predictions.csv`
- gold audit source: `data\v1\gold\heldout_full_extraction_gold_v2_adjudicated.csv`
- role taxonomies: `src/role_taxonomies.py` coarse_5/coarse_4/coarse_3 mappings
- correctness definitions mirror `src/evaluate_llm_extraction_predictions.py` rows 55-68
