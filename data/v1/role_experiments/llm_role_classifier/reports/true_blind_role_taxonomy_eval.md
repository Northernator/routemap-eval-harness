# Role Taxonomy Level Evaluation

## Model x Taxonomy Accuracy

| model | fine_8 | coarse_5 | coarse_4 | coarse_3 |
|---|---|---|---|---|
| pred_role_llm | 0.556 | 0.625 | 0.639 | 0.681 |
| pred_role_baseline | 0.125 | 0.167 | 0.181 | 0.319 |

## Best Model Per Taxonomy

| taxonomy | best_model | accuracy |
|---|---|---:|
| fine_8 | pred_role_llm | 0.556 |
| coarse_5 | pred_role_llm | 0.625 |
| coarse_4 | pred_role_llm | 0.639 |
| coarse_3 | pred_role_llm | 0.681 |

## Best Taxonomy Per Model

| model | best_taxonomy | accuracy |
|---|---|---:|
| pred_role_llm | coarse_3 | 0.681 |
| pred_role_baseline | coarse_3 | 0.319 |

## fine_8: `pred_role_llm`

| gold\pred | BACKGROUND | CLAIM | DEFINE | EXAMPLE | LIMITATION | METHOD | NEXT_STEP | RESULT |
|---|---|---|---|---|---|---|---|---|
| BACKGROUND | 0 | 5 | 2 | 0 | 5 | 0 | 0 | 0 |
| CLAIM | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| DEFINE | 0 | 0 | 11 | 0 | 0 | 1 | 0 | 0 |
| EXAMPLE | 0 | 2 | 0 | 1 | 0 | 1 | 0 | 0 |
| LIMITATION | 0 | 4 | 0 | 0 | 4 | 4 | 0 | 0 |
| METHOD | 0 | 0 | 0 | 0 | 0 | 15 | 0 | 0 |
| NEXT_STEP | 0 | 0 | 0 | 0 | 0 | 5 | 4 | 0 |
| RESULT | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 5 |

## coarse_5: `pred_role_llm`

| gold\pred | ACTION | ASSERTION | CAVEAT | CONTEXT | INSTANCE |
|---|---|---|---|---|---|
| ACTION | 24 | 0 | 0 | 0 | 0 |
| ASSERTION | 1 | 16 | 3 | 0 | 0 |
| CAVEAT | 4 | 4 | 4 | 0 | 0 |
| CONTEXT | 0 | 7 | 5 | 0 | 0 |
| INSTANCE | 1 | 2 | 0 | 0 | 1 |

## coarse_4: `pred_role_llm`

| gold\pred | ACTION | CAVEAT | CONTENT | CONTEXT |
|---|---|---|---|---|
| ACTION | 26 | 0 | 2 | 0 |
| CAVEAT | 4 | 4 | 4 | 0 |
| CONTENT | 1 | 3 | 16 | 0 |
| CONTEXT | 0 | 5 | 7 | 0 |

## coarse_3: `pred_role_llm`

| gold\pred | CAVEAT | CONTEXT | SUBSTANTIVE |
|---|---|---|---|
| CAVEAT | 4 | 0 | 8 |
| CONTEXT | 5 | 0 | 7 |
| SUBSTANTIVE | 3 | 0 | 45 |

## Interpretation

Fine and coarse scores should both be reported. Coarse taxonomy gains indicate that models have route-function signal even when they miss fine-grained role boundaries.