# Role Taxonomy Level Evaluation

## Model x Taxonomy Accuracy

| model | fine_8 | coarse_5 | coarse_4 | coarse_3 |
|---|---|---|---|---|
| pred_role_llm | 0.825 | 0.850 | 0.912 | 0.938 |
| pred_role_baseline | 0.525 | 0.600 | 0.613 | 0.775 |

## Best Model Per Taxonomy

| taxonomy | best_model | accuracy |
|---|---|---:|
| fine_8 | pred_role_llm | 0.825 |
| coarse_5 | pred_role_llm | 0.850 |
| coarse_4 | pred_role_llm | 0.912 |
| coarse_3 | pred_role_llm | 0.938 |

## Best Taxonomy Per Model

| model | best_taxonomy | accuracy |
|---|---|---:|
| pred_role_llm | coarse_3 | 0.938 |
| pred_role_baseline | coarse_3 | 0.775 |

## fine_8: `pred_role_llm`

| gold\pred | BACKGROUND | CLAIM | DEFINE | EXAMPLE | LIMITATION | METHOD | NEXT_STEP | RESULT |
|---|---|---|---|---|---|---|---|---|
| BACKGROUND | 9 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| CLAIM | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| DEFINE | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 |
| EXAMPLE | 0 | 2 | 0 | 3 | 0 | 3 | 2 | 0 |
| LIMITATION | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 |
| METHOD | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 |
| NEXT_STEP | 0 | 0 | 0 | 0 | 0 | 2 | 8 | 0 |
| RESULT | 1 | 0 | 0 | 0 | 3 | 0 | 0 | 6 |

## coarse_5: `pred_role_llm`

| gold\pred | ACTION | ASSERTION | CAVEAT | CONTEXT | INSTANCE |
|---|---|---|---|---|---|
| ACTION | 20 | 0 | 0 | 0 | 0 |
| ASSERTION | 0 | 26 | 3 | 1 | 0 |
| CAVEAT | 0 | 0 | 10 | 0 | 0 |
| CONTEXT | 0 | 1 | 0 | 9 | 0 |
| INSTANCE | 5 | 2 | 0 | 0 | 3 |

## coarse_4: `pred_role_llm`

| gold\pred | ACTION | CAVEAT | CONTENT | CONTEXT |
|---|---|---|---|---|
| ACTION | 28 | 0 | 2 | 0 |
| CAVEAT | 0 | 10 | 0 | 0 |
| CONTENT | 0 | 3 | 26 | 1 |
| CONTEXT | 0 | 0 | 1 | 9 |

## coarse_3: `pred_role_llm`

| gold\pred | CAVEAT | CONTEXT | SUBSTANTIVE |
|---|---|---|---|
| CAVEAT | 10 | 0 | 0 |
| CONTEXT | 0 | 9 | 1 |
| SUBSTANTIVE | 3 | 1 | 56 |

## Interpretation

Fine and coarse scores should both be reported. Coarse taxonomy gains indicate that models have route-function signal even when they miss fine-grained role boundaries.