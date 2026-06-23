# True-Blind R6 Candidate Audit

## Audit Answers

| question | answer |
|---|---|
| A. Does R6 beat combined_v3 on role? | NO |
| B. Does R6 preserve combined_v3 coarse_3? | YES |
| C. Does R6 beat combined_v3 on relaxed_1? | NO |
| D. Does R6 match or beat combined_v3 on relaxed_2? | YES |
| E. Does R6 match combined_v3 on relaxed_3? | YES |
| F. Does R6 lose strict accuracy? | NO |
| G. Is entity exact still the main strict blocker? | YES |
| H. Is relation still secondary? | YES |
| I. Is there evidence R6 overfit earlier splits? | NO |
| J. Should R6 be promoted as RouteMap v2 default candidate? | NO |

## Metrics

| variant | role | coarse_5 | coarse_4 | coarse_3 | entity_jaccard | entity_exact | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| combined_v3 | 0.306 | 0.347 | 0.361 | 0.556 | 0.000 | 0.000 | 0.542 | 0.222 | 0.819 | 0.000 | 0.000 | 0.000 | 0.000 |
| D | 0.236 | 0.236 | 0.236 | 0.306 | 0.000 | 0.000 | 0.361 | 0.222 | 0.819 | 0.000 | 0.000 | 0.000 | 0.000 |
| R6 | 0.306 | 0.333 | 0.347 | 0.556 | 0.000 | 0.000 | 0.542 | 0.222 | 0.819 | 0.000 | 0.000 | 0.000 | 0.000 |

## R6 Strict Blockers

| blocker | rows |
|---|---|
| entity | 72 |
| relation | 56 |
| status | 33 |
| role | 50 |
| answer | 13 |
| multiple | 60 |

## Outcome Buckets

| outcome_bucket | rows |
|---|---|
| multi_field_blocks_R6 | 43 |
| R6_role_repair_success | 15 |
| R6_role_repair_failure | 10 |
| entity_blocks_R6 | 4 |

## Role Guard Counts

| measure | rows |
|---|---|
| coarse_3_guard_changed_D_role | 48 |
| R6_fine_role_correct_but_strict_fails | 22 |

## Final Verdict

keep R6 provisional pending more true-blind rows
