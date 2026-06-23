# Natural Blind R6 Candidate Audit

## Audit Answers

| question | answer |
|---|---|
| A. R6 beats combined_v3 on role | NO |
| B. R6 preserves/improves combined_v3 coarse_3 | YES |
| C. R6 beats combined_v3 on relaxed_1 | NO |
| D. R6 matches/beats combined_v3 on relaxed_2 | YES |
| E. R6 matches/beats combined_v3 on relaxed_3 | YES |
| F. R6 loses strict compared with combined_v3 | NO |
| G. coarse_3 guard helps more than hurts | YES |
| H. entity exact remains main strict blocker | YES |
| I. relation remains secondary blocker | YES |
| J. evidence R6 overfit calibration or boundary-stress data | NO |

## Metrics

| variant | role | coarse_3 | entity J | entity exact | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| combined_v3 | 0.990 | 0.990 | 0.235 | 0.030 | 0.970 | 0.889 | 0.889 | 0.010 | 0.172 | 0.172 | 0.172 |
| D | 0.343 | 0.394 | 0.235 | 0.030 | 0.636 | 0.333 | 0.889 | 0.000 | 0.040 | 0.061 | 0.061 |
| R6 | 0.939 | 0.990 | 0.235 | 0.030 | 0.970 | 0.889 | 0.889 | 0.010 | 0.152 | 0.172 | 0.172 |

## Row Buckets

| outcome_bucket | rows |
|---|---|
| R6_role_repair_success | 49 |
| entity_blocks_R6 | 22 |
| multi_field_blocks_R6 | 16 |
| R6_preserves_combined_relaxed3 | 11 |
| R6_role_repair_failure | 1 |

## R6 Strict Blockers

| blocker | rows |
|---|---|
| entity | 96 |
| relation | 11 |
| status | 3 |
| role | 6 |
| answer | 11 |
| multiple | 27 |

## Role Repair Counts

| measure | rows |
|---|---|
| coarse_3_guard_changed_D_role | 61 |
| changes_helped | 11 |
| changes_hurt | 0 |
| changes_improved_fine_role | 60 |
| changes_improved_coarse3_only | 0 |
| R6_fine_role_correct_but_strict_fails | 92 |

## Final Verdict

keep R6 provisional pending more data

This audit uses a 99-row constructed pseudo-blind natural route-note split. It is larger and more natural than EXPAND boundary-stress rows, and it excludes HELDOUT2 calibration and EXPAND heldout segment IDs, but it is not a true newly collected blind benchmark.
