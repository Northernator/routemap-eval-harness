# Heldout R6 Candidate Audit

## Audit Answers

| question | answer |
|---|---|
| A. R6 beats combined_v3 on relaxed_1 | YES |
| B. R6 matches/beats combined_v3 on relaxed_2 | YES |
| C. R6 matches/beats combined_v3 on relaxed_3 | YES |
| D. R6 does not lose strict vs combined_v3 | YES |
| E. R6 improves fine-role accuracy | YES |
| F. coarse_3 guard helps more than hurts | YES |
| G. entity exact failures remain main strict blocker | YES |
| H. relation remains secondary blocker | YES |
| I. evidence R6 overfit calibration set | NO |

## Metrics

| variant | role | coarse_3 | entity J | entity exact | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| combined_v3 | 0.476 | 0.833 | 0.459 | 0.048 | 0.619 | 0.476 | 0.786 | 0.024 | 0.179 | 0.274 | 0.345 |
| D | 0.500 | 0.512 | 0.459 | 0.048 | 0.667 | 0.476 | 0.786 | 0.036 | 0.167 | 0.167 | 0.167 |
| R6 | 0.595 | 0.833 | 0.459 | 0.048 | 0.619 | 0.476 | 0.786 | 0.024 | 0.262 | 0.310 | 0.345 |

## Row Buckets

| outcome_bucket | rows |
|---|---|
| R6_preserves_combined_relaxed3 | 16 |
| multi_field_blocks_R6 | 16 |
| entity_blocks_R6 | 15 |
| R6_coarse_guard_saved_row | 12 |
| R6_role_repair_failure | 9 |
| R6_role_repair_success | 8 |
| R6_relaxed1_gain | 5 |
| D_strict_win | 2 |
| all_strict_correct | 1 |

## R6 Strict Blockers

| blocker | rows |
|---|---|
| entity | 80 |
| relation | 44 |
| status | 32 |
| role | 34 |
| answer | 18 |
| multiple | 51 |

## Role Repair Counts

| measure | rows |
|---|---|
| coarse_3_guard_changed_D_role | 46 |
| changes_helped | 16 |
| changes_hurt | 1 |
| changes_improved_fine_role | 17 |
| changes_improved_coarse3_only | 19 |
| R6_fine_role_correct_but_strict_fails | 48 |

## Final Verdict

promote R6 as RouteMap v2 candidate

This audit uses the existing 84-row `expanded_test_v2` split, with no `HELDOUT2` calibration segment overlap. Predictions were generated before evaluation; gold labels were used only for scoring and audit labels.
