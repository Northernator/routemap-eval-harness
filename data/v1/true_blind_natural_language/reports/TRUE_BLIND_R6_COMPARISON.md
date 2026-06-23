# True-Blind R6 Comparison

Gold labels were frozen before predictions. This report must not be used to tune combined_v3, D, R6, prompts, taxonomies, mappings, thresholds, or evaluator logic.

## Metrics

| variant | evaluated_rows | missing_invalid_rows | role | coarse_5 | coarse_4 | coarse_3 | entity_jaccard | entity_exact | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| combined_v3 | 72 | 0 | 0.306 | 0.347 | 0.361 | 0.556 | 0.000 | 0.000 | 0.542 | 0.222 | 0.819 | 0.000 | 0.000 | 0.000 | 0.000 |
| D_add_combined_answer | 72 | 0 | 0.236 | 0.236 | 0.236 | 0.306 | 0.000 | 0.000 | 0.361 | 0.222 | 0.819 | 0.000 | 0.000 | 0.000 | 0.000 |
| R6 | 72 | 0 | 0.306 | 0.333 | 0.347 | 0.556 | 0.000 | 0.000 | 0.542 | 0.222 | 0.819 | 0.000 | 0.000 | 0.000 | 0.000 |

## R6 Checks

| check | passed |
|---|---:|
| role_beats_combined | NO |
| coarse_3_preserved_or_improved | YES |
| relaxed_1_beats_combined | NO |
| relaxed_2_matches_or_beats_combined | YES |
| relaxed_3_matches_combined | YES |
| strict_not_lower_than_combined | YES |

## Final Verdict

keep R6 provisional pending more true-blind rows
