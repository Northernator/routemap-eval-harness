# Heldout R6 Generalisation Comparison

## Metrics

| variant | evaluated_rows | missing_invalid_rows | role | coarse_5 | coarse_4 | coarse_3 | entity_jaccard | entity_exact | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| combined_v3 | 84 | 0 | 0.476 | 0.595 | 0.619 | 0.833 | 0.459 | 0.048 | 0.619 | 0.476 | 0.786 | 0.024 | 0.179 | 0.274 | 0.345 |
| D_add_combined_answer | 84 | 0 | 0.500 | 0.500 | 0.500 | 0.512 | 0.459 | 0.048 | 0.667 | 0.476 | 0.786 | 0.036 | 0.167 | 0.167 | 0.167 |
| R6 | 84 | 0 | 0.595 | 0.655 | 0.679 | 0.833 | 0.459 | 0.048 | 0.619 | 0.476 | 0.786 | 0.024 | 0.262 | 0.310 | 0.345 |

## Calibration Targets

| variant | role | coarse_3 | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---:|---:|---:|---:|---:|---:|
| combined_v3 | 0.532 | 0.823 | 0.051 | 0.253 | 0.354 | 0.443 |
| R6 | 0.709 | 0.823 | 0.051 | 0.354 | 0.392 | 0.443 |

## R6 Generalisation Checks

| check | passed |
|---|---:|
| role_beats_combined | YES |
| relaxed_1_beats_combined | YES |
| relaxed_2_matches_or_beats_combined | YES |
| relaxed_3_matches_or_beats_combined | YES |
| strict_not_lower_than_combined | YES |

## Final Verdict

promote R6 as RouteMap v2 candidate

The heldout split is `data/v1/gold/expanded_test_v2.csv`, an existing 84-row full-extraction test split with no HELDOUT2 calibration segment overlap.
