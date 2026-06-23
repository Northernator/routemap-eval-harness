# FULL_EXTRACTION_LLM_REAL_ROUTE_REPORT

Offline diagnostic read. Cached LLM entity spans are reused; no provider calls are made.

## true_blind_combined_v3

| variant | route_mode | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role_accuracy | frac_softj_ge_0_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_v0 | real-route | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | NA |
| baseline_v0 | real-route | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.000000 |
| baseline_v0 | real-route | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.000000 |
| v2_reference | real-route | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | NA |
| v2_reference | real-route | soft-difflib | 0.127552 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.013889 |
| v2_reference | real-route | soft-embedding | 0.170211 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.027778 |
| llm_open | real-route | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | NA |
| llm_open | real-route | soft-difflib | 0.150959 | 0.000000 | 0.041667 | 0.055556 | 0.125000 | 0.305556 | 0.180556 |
| llm_open | real-route | soft-embedding | 0.159061 | 0.000000 | 0.041667 | 0.055556 | 0.125000 | 0.305556 | 0.180556 |
| llm_adaptive | real-route | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | NA |
| llm_adaptive | real-route | soft-difflib | 0.127976 | 0.000000 | 0.027778 | 0.027778 | 0.083333 | 0.305556 | 0.125000 |
| llm_adaptive | real-route | soft-embedding | 0.136872 | 0.000000 | 0.027778 | 0.027778 | 0.083333 | 0.305556 | 0.125000 |
| gold_other_llm_open | gold-other | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA |
| gold_other_llm_open | gold-other | soft-difflib | 0.150959 | 0.041667 | 0.180556 | 0.180556 | 0.180556 | 1.000000 | 0.180556 |
| gold_other_llm_open | gold-other | soft-embedding | 0.159061 | 0.069444 | 0.180556 | 0.180556 | 0.180556 | 1.000000 | 0.180556 |
| gold_other_llm_adaptive | gold-other | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA |
| gold_other_llm_adaptive | gold-other | soft-difflib | 0.127976 | 0.027778 | 0.125000 | 0.125000 | 0.125000 | 1.000000 | 0.125000 |
| gold_other_llm_adaptive | gold-other | soft-embedding | 0.136872 | 0.055556 | 0.125000 | 0.125000 | 0.125000 | 1.000000 | 0.125000 |

## true_blind_R6

| variant | route_mode | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role_accuracy | frac_softj_ge_0_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_v0 | real-route | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | NA |
| baseline_v0 | real-route | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.000000 |
| baseline_v0 | real-route | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.000000 |
| v2_reference | real-route | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | NA |
| v2_reference | real-route | soft-difflib | 0.127552 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.013889 |
| v2_reference | real-route | soft-embedding | 0.170211 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.027778 |
| llm_open | real-route | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | NA |
| llm_open | real-route | soft-difflib | 0.150959 | 0.000000 | 0.041667 | 0.041667 | 0.125000 | 0.305556 | 0.180556 |
| llm_open | real-route | soft-embedding | 0.159061 | 0.000000 | 0.041667 | 0.041667 | 0.125000 | 0.305556 | 0.180556 |
| llm_adaptive | real-route | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | NA |
| llm_adaptive | real-route | soft-difflib | 0.127976 | 0.000000 | 0.027778 | 0.027778 | 0.083333 | 0.305556 | 0.125000 |
| llm_adaptive | real-route | soft-embedding | 0.136872 | 0.000000 | 0.027778 | 0.027778 | 0.083333 | 0.305556 | 0.125000 |
| gold_other_llm_open | gold-other | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA |
| gold_other_llm_open | gold-other | soft-difflib | 0.150959 | 0.041667 | 0.180556 | 0.180556 | 0.180556 | 1.000000 | 0.180556 |
| gold_other_llm_open | gold-other | soft-embedding | 0.159061 | 0.069444 | 0.180556 | 0.180556 | 0.180556 | 1.000000 | 0.180556 |
| gold_other_llm_adaptive | gold-other | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA |
| gold_other_llm_adaptive | gold-other | soft-difflib | 0.127976 | 0.027778 | 0.125000 | 0.125000 | 0.125000 | 1.000000 | 0.125000 |
| gold_other_llm_adaptive | gold-other | soft-embedding | 0.136872 | 0.055556 | 0.125000 | 0.125000 | 0.125000 | 1.000000 | 0.125000 |

## dev

| variant | route_mode | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role_accuracy | frac_softj_ge_0_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_v0 | real-route | exact | 0.719792 | 0.487500 | 0.837500 | 0.837500 | 0.837500 | 0.987500 | NA |
| baseline_v0 | real-route | soft-difflib | 0.711667 | 0.475000 | 0.837500 | 0.837500 | 0.837500 | 0.987500 | 0.850000 |
| baseline_v0 | real-route | soft-embedding | 0.714345 | 0.475000 | 0.837500 | 0.837500 | 0.837500 | 0.987500 | 0.850000 |
| v2_reference | real-route | exact | 0.452083 | 0.225000 | 0.525000 | 0.525000 | 0.525000 | 0.987500 | NA |
| v2_reference | real-route | soft-difflib | 0.472991 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 |
| v2_reference | real-route | soft-embedding | 0.474702 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 |
| llm_open | real-route | exact | 0.021250 | 0.000000 | 0.025000 | 0.025000 | 0.025000 | 0.987500 | NA |
| llm_open | real-route | soft-difflib | 0.064167 | 0.012500 | 0.062500 | 0.062500 | 0.062500 | 0.987500 | 0.062500 |
| llm_open | real-route | soft-embedding | 0.087083 | 0.012500 | 0.087500 | 0.087500 | 0.087500 | 0.987500 | 0.087500 |
| llm_adaptive | real-route | exact | 0.452083 | 0.225000 | 0.525000 | 0.525000 | 0.525000 | 0.987500 | NA |
| llm_adaptive | real-route | soft-difflib | 0.478512 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 |
| llm_adaptive | real-route | soft-embedding | 0.471429 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 |
| gold_other_llm_open | gold-other | exact | 0.021250 | 0.012500 | 0.025000 | 0.025000 | 0.025000 | 1.000000 | NA |
| gold_other_llm_open | gold-other | soft-difflib | 0.064167 | 0.012500 | 0.062500 | 0.062500 | 0.062500 | 1.000000 | 0.062500 |
| gold_other_llm_open | gold-other | soft-embedding | 0.087083 | 0.025000 | 0.087500 | 0.087500 | 0.087500 | 1.000000 | 0.087500 |
| gold_other_llm_adaptive | gold-other | exact | 0.452083 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 1.000000 | NA |
| gold_other_llm_adaptive | gold-other | soft-difflib | 0.478512 | 0.275000 | 0.550000 | 0.550000 | 0.550000 | 1.000000 | 0.550000 |
| gold_other_llm_adaptive | gold-other | soft-embedding | 0.471429 | 0.275000 | 0.550000 | 0.550000 | 0.550000 | 1.000000 | 0.550000 |

## Verdicts

| real_outdomain_relaxed_moves | entity_vs_route_gap | entity_vs_route_gap_max | roles_now_dominant_blocker | adaptive_best_both | best_true_blind_real_route | best_true_blind_gold_other |
| --- | --- | --- | --- | --- | --- | --- |
| true | {'true_blind_combined_v3__llm_open': 0.1388888888888889, 'true_blind_combined_v3__llm_adaptive': 0.09722222222222222, 'true_blind_R6__llm_open': 0.1388888888888889, 'true_blind_R6__llm_adaptive': 0.09722222222222222} | 0.138889 | true | true | {'dataset': 'true_blind_combined_v3', 'variant': 'llm_open', 'relaxed_1': 0.041666666666666664} | {'dataset': 'true_blind_combined_v3', 'variant': 'gold_other_llm_open', 'relaxed_1': 0.18055555555555555} |

## Recommendation

Adopt llm_adaptive as the single entity variant: it preserves dev performance against v2 and stays within tolerance of llm_open out-of-domain. LLM entities move real out-of-domain full-row off zero, but route fields now dominate the remaining loss. Next step: run a roles-focused phase, then use a fresh blind split for the final headline number.