# Natural Blind R6 Generalisation Comparison

## Metrics

| variant | evaluated_rows | missing_invalid_rows | role | coarse_5 | coarse_4 | coarse_3 | entity_jaccard | entity_exact | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| combined_v3 | 99 | 0 | 0.990 | 0.990 | 0.990 | 0.990 | 0.235 | 0.030 | 0.970 | 0.889 | 0.889 | 0.010 | 0.172 | 0.172 | 0.172 |
| D_add_combined_answer | 99 | 0 | 0.343 | 0.364 | 0.364 | 0.394 | 0.235 | 0.030 | 0.636 | 0.333 | 0.889 | 0.000 | 0.040 | 0.061 | 0.061 |
| R6 | 99 | 0 | 0.939 | 0.960 | 0.960 | 0.990 | 0.235 | 0.030 | 0.970 | 0.889 | 0.889 | 0.010 | 0.152 | 0.172 | 0.172 |

## R6 Generalisation Checks

| check | passed |
|---|---:|
| role_beats_combined | NO |
| coarse_3_preserved_or_improved | YES |
| relaxed_1_beats_combined | NO |
| relaxed_2_matches_or_beats_combined | YES |
| relaxed_3_matches_or_beats_combined | YES |
| strict_not_lower_than_combined | YES |

## Final Verdict

keep R6 provisional pending more data

The split is `data/v1/heldout/natural_language_blind/natural_language_blind_gold.csv`: a 99-row constructed pseudo-blind natural route-note split. It is distinct from HELDOUT2 calibration and EXPAND boundary-stress rows, but it is not a true newly collected blind benchmark.
