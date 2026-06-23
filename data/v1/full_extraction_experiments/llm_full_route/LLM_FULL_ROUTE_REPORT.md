# LLM_FULL_ROUTE_REPORT

Offline diagnostic read. Cached LLM role and entity outputs are reused; no provider calls are made.

## Prior reference points

| true_blind_original_relaxed_1 | combined_v3_llm_entities_relaxed_1 | combined_v3_llm_entities_relaxed_3 | entity_only_ceiling |
| --- | --- | --- | --- |
| 0.000000 | 0.042000 | 0.125000 | 0.181000 |

## true_blind_combined_v3

| variant | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role8_accuracy | role_coarse3_accuracy | answer_accuracy | frac_jaccard_ge_0_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORIGINAL | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.555556 | 0.819444 | 0.000000 |
| ORIGINAL | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.555556 | 0.819444 | 0.000000 |
| ORIGINAL | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.555556 | 0.819444 | 0.000000 |
| ROLE_LLM_ONLY | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| ROLE_LLM_ONLY | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| ROLE_LLM_ONLY | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| ENT_LLM_ONLY | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.555556 | 0.819444 | 0.000000 |
| ENT_LLM_ONLY | soft-difflib | 0.127976 | 0.000000 | 0.027778 | 0.027778 | 0.083333 | 0.305556 | 0.555556 | 0.819444 | 0.125000 |
| ENT_LLM_ONLY | soft-embedding | 0.136872 | 0.000000 | 0.027778 | 0.027778 | 0.083333 | 0.305556 | 0.555556 | 0.819444 | 0.125000 |
| FULL_LLM_adaptive | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| FULL_LLM_adaptive | soft-difflib | 0.127976 | 0.000000 | 0.055556 | 0.055556 | 0.055556 | 0.555556 | 0.680556 | 0.819444 | 0.125000 |
| FULL_LLM_adaptive | soft-embedding | 0.136872 | 0.000000 | 0.055556 | 0.055556 | 0.055556 | 0.555556 | 0.680556 | 0.819444 | 0.125000 |
| FULL_LLM_open | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| FULL_LLM_open | soft-difflib | 0.150959 | 0.000000 | 0.083333 | 0.111111 | 0.111111 | 0.555556 | 0.680556 | 0.819444 | 0.180556 |
| FULL_LLM_open | soft-embedding | 0.159061 | 0.000000 | 0.083333 | 0.111111 | 0.111111 | 0.555556 | 0.680556 | 0.819444 | 0.180556 |
| DIAGNOSTIC_gold_other | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 1.000000 | 0.000000 |
| DIAGNOSTIC_gold_other | soft-difflib | 0.127976 | 0.013889 | 0.069444 | 0.069444 | 0.083333 | 0.555556 | 0.680556 | 1.000000 | 0.125000 |
| DIAGNOSTIC_gold_other | soft-embedding | 0.136872 | 0.041667 | 0.069444 | 0.069444 | 0.083333 | 0.555556 | 0.680556 | 1.000000 | 0.125000 |

## true_blind_R6

| variant | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role8_accuracy | role_coarse3_accuracy | answer_accuracy | frac_jaccard_ge_0_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORIGINAL | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.555556 | 0.819444 | 0.000000 |
| ORIGINAL | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.555556 | 0.819444 | 0.000000 |
| ORIGINAL | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.555556 | 0.819444 | 0.000000 |
| ROLE_LLM_ONLY | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| ROLE_LLM_ONLY | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| ROLE_LLM_ONLY | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| ENT_LLM_ONLY | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.305556 | 0.555556 | 0.819444 | 0.000000 |
| ENT_LLM_ONLY | soft-difflib | 0.127976 | 0.000000 | 0.027778 | 0.027778 | 0.083333 | 0.305556 | 0.555556 | 0.819444 | 0.125000 |
| ENT_LLM_ONLY | soft-embedding | 0.136872 | 0.000000 | 0.027778 | 0.027778 | 0.083333 | 0.305556 | 0.555556 | 0.819444 | 0.125000 |
| FULL_LLM_adaptive | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| FULL_LLM_adaptive | soft-difflib | 0.127976 | 0.000000 | 0.055556 | 0.055556 | 0.055556 | 0.555556 | 0.680556 | 0.819444 | 0.125000 |
| FULL_LLM_adaptive | soft-embedding | 0.136872 | 0.000000 | 0.055556 | 0.055556 | 0.055556 | 0.555556 | 0.680556 | 0.819444 | 0.125000 |
| FULL_LLM_open | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 0.819444 | 0.000000 |
| FULL_LLM_open | soft-difflib | 0.150959 | 0.000000 | 0.083333 | 0.111111 | 0.111111 | 0.555556 | 0.680556 | 0.819444 | 0.180556 |
| FULL_LLM_open | soft-embedding | 0.159061 | 0.000000 | 0.083333 | 0.111111 | 0.111111 | 0.555556 | 0.680556 | 0.819444 | 0.180556 |
| DIAGNOSTIC_gold_other | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.555556 | 0.680556 | 1.000000 | 0.000000 |
| DIAGNOSTIC_gold_other | soft-difflib | 0.127976 | 0.013889 | 0.069444 | 0.069444 | 0.083333 | 0.555556 | 0.680556 | 1.000000 | 0.125000 |
| DIAGNOSTIC_gold_other | soft-embedding | 0.136872 | 0.041667 | 0.069444 | 0.069444 | 0.083333 | 0.555556 | 0.680556 | 1.000000 | 0.125000 |

## dev

| variant | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role8_accuracy | role_coarse3_accuracy | answer_accuracy | frac_jaccard_ge_0_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORIGINAL | exact | 0.719792 | 0.487500 | 0.837500 | 0.837500 | 0.837500 | 0.987500 | 0.987500 | 1.000000 | 0.850000 |
| ORIGINAL | soft-difflib | 0.711667 | 0.475000 | 0.837500 | 0.837500 | 0.837500 | 0.987500 | 0.987500 | 1.000000 | 0.850000 |
| ORIGINAL | soft-embedding | 0.714345 | 0.475000 | 0.837500 | 0.837500 | 0.837500 | 0.987500 | 0.987500 | 1.000000 | 0.850000 |
| ROLE_LLM_ONLY | exact | 0.719792 | 0.425000 | 0.700000 | 0.787500 | 0.812500 | 0.825000 | 0.937500 | 1.000000 | 0.850000 |
| ROLE_LLM_ONLY | soft-difflib | 0.711667 | 0.425000 | 0.700000 | 0.787500 | 0.812500 | 0.825000 | 0.937500 | 1.000000 | 0.850000 |
| ROLE_LLM_ONLY | soft-embedding | 0.714345 | 0.425000 | 0.700000 | 0.787500 | 0.812500 | 0.825000 | 0.937500 | 1.000000 | 0.850000 |
| ENT_LLM_ONLY | exact | 0.424583 | 0.212500 | 0.500000 | 0.500000 | 0.500000 | 0.987500 | 0.987500 | 1.000000 | 0.512500 |
| ENT_LLM_ONLY | soft-difflib | 0.451012 | 0.237500 | 0.512500 | 0.512500 | 0.512500 | 0.987500 | 0.987500 | 1.000000 | 0.525000 |
| ENT_LLM_ONLY | soft-embedding | 0.443929 | 0.237500 | 0.512500 | 0.512500 | 0.512500 | 0.987500 | 0.987500 | 1.000000 | 0.525000 |
| FULL_LLM_adaptive | exact | 0.424583 | 0.200000 | 0.425000 | 0.475000 | 0.500000 | 0.825000 | 0.937500 | 1.000000 | 0.512500 |
| FULL_LLM_adaptive | soft-difflib | 0.451012 | 0.225000 | 0.437500 | 0.500000 | 0.512500 | 0.825000 | 0.937500 | 1.000000 | 0.525000 |
| FULL_LLM_adaptive | soft-embedding | 0.443929 | 0.225000 | 0.437500 | 0.500000 | 0.512500 | 0.825000 | 0.937500 | 1.000000 | 0.525000 |
| FULL_LLM_open | exact | 0.021250 | 0.000000 | 0.012500 | 0.025000 | 0.025000 | 0.825000 | 0.937500 | 1.000000 | 0.025000 |
| FULL_LLM_open | soft-difflib | 0.064167 | 0.000000 | 0.037500 | 0.050000 | 0.062500 | 0.825000 | 0.937500 | 1.000000 | 0.062500 |
| FULL_LLM_open | soft-embedding | 0.087083 | 0.000000 | 0.062500 | 0.075000 | 0.087500 | 0.825000 | 0.937500 | 1.000000 | 0.087500 |
| DIAGNOSTIC_gold_other | exact | 0.424583 | 0.225000 | 0.425000 | 0.475000 | 0.500000 | 0.825000 | 0.937500 | 1.000000 | 0.512500 |
| DIAGNOSTIC_gold_other | soft-difflib | 0.451012 | 0.250000 | 0.437500 | 0.500000 | 0.512500 | 0.825000 | 0.937500 | 1.000000 | 0.525000 |
| DIAGNOSTIC_gold_other | soft-embedding | 0.443929 | 0.250000 | 0.437500 | 0.500000 | 0.512500 | 0.825000 | 0.937500 | 1.000000 | 0.525000 |

## Verdicts

```json
{
  "approaches_entity_ceiling": false,
  "background_gold_rows": 12,
  "background_to_claim_count": 5,
  "best_true_blind_full_llm_relaxed1": {
    "dataset": "true_blind_combined_v3",
    "relaxed_1": 0.08333333333333333,
    "relaxed_3": 0.1111111111111111,
    "variant": "FULL_LLM_open"
  },
  "full_llm_relaxed1_beats_prior": true,
  "full_llm_relaxed3_dataset": "true_blind_combined_v3",
  "full_llm_relaxed3_value": 0.1111111111111111,
  "full_llm_relaxed3_variant": "FULL_LLM_open",
  "indomain_no_regression": false,
  "role_llm_contribution": 0.0,
  "role_llm_contribution_by_dataset": {
    "true_blind_R6": 0.0,
    "true_blind_combined_v3": 0.0
  }
}
```

## Recommendation

Do not lock the combined LLM RouteMap as the sole configuration yet. Fresh blind split is warranted for a clean headline after this diagnostic read. The run still sits below the entity-only ceiling, so entity coverage plus residual route fields remain binding.