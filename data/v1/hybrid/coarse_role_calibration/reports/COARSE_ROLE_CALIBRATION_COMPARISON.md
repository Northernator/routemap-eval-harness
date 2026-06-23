# Coarse Role Calibration Comparison

## Metrics

| variant | role | coarse_5 | coarse_4 | coarse_3 | entity_jaccard | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| combined_v3 | 0.532 | 0.620 | 0.696 | 0.823 | 0.506 | 0.595 | 0.443 | 0.848 | 0.051 | 0.253 | 0.354 | 0.443 |
| D_add_combined_answer | 0.595 | 0.595 | 0.595 | 0.608 | 0.506 | 0.658 | 0.430 | 0.848 | 0.025 | 0.304 | 0.304 | 0.316 |
| R0_D_baseline_copy | 0.595 | 0.595 | 0.595 | 0.608 | 0.506 | 0.658 | 0.430 | 0.848 | 0.025 | 0.304 | 0.304 | 0.316 |
| R1_combined_role_fallback_on_disagreement | 0.532 | 0.620 | 0.696 | 0.823 | 0.506 | 0.658 | 0.430 | 0.848 | 0.025 | 0.253 | 0.354 | 0.443 |
| R2_coarse3_guard | 0.709 | 0.734 | 0.772 | 0.823 | 0.506 | 0.658 | 0.430 | 0.848 | 0.025 | 0.354 | 0.392 | 0.443 |
| R3_coarse4_guard | 0.620 | 0.646 | 0.696 | 0.823 | 0.506 | 0.658 | 0.430 | 0.848 | 0.025 | 0.304 | 0.354 | 0.443 |
| R4_coarse5_guard | 0.595 | 0.620 | 0.696 | 0.823 | 0.506 | 0.658 | 0.430 | 0.848 | 0.025 | 0.291 | 0.354 | 0.443 |
| R5_coarse3_guard_combined_relation | 0.709 | 0.734 | 0.772 | 0.823 | 0.506 | 0.658 | 0.443 | 0.848 | 0.038 | 0.354 | 0.392 | 0.443 |
| R6_coarse3_guard_combined_status_relation | 0.709 | 0.734 | 0.772 | 0.823 | 0.506 | 0.595 | 0.443 | 0.848 | 0.051 | 0.354 | 0.392 | 0.443 |

## Interpretation

Best strict: combined_v3, R6_coarse3_guard_combined_status_relation = 0.051.
Best relaxed_1: R2_coarse3_guard = 0.354.
Best relaxed_2: R2_coarse3_guard = 0.392.
Best relaxed_3: combined_v3 = 0.443.

Exact disagreement fallback does not preserve D's relaxed_1 gain. Coarse_3 guarding preserves and improves it while recovering combined_v3's relaxed_3 score.
The coarse_3 guard beats both D and combined_v3 on relaxed_1 and relaxed_2, and ties combined_v3 on relaxed_3.
Among role guards, coarse_3 is the best relaxed_1/2/3 compromise. Coarse_4 and coarse_5 recover coarse scores but lose more fine-role gain.
Adding combined_v3 relation improves relation accuracy but does not improve strict because exact entity match and other field interactions still block rows.
Adding combined_v3 status plus relation improves status but not strict beyond relation alone in this run.
Best current RouteMap v2 candidate from this test is R6_coarse3_guard_combined_status_relation for full extraction: it keeps R2's relaxed balance and recovers strict accuracy to the combined_v3 level. R2 remains the cleanest role-only calibration.
