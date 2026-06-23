# P1 Role Adjudication Summary

- Total P1 rows: 31
- ACCEPT_GOLD: 30
- CHANGE_GOLD: 0
- NEEDS_SECOND_REVIEW: 1
- RUBRIC_AMBIGUOUS: 0

## Count By Adjudicated Role

| adjudicated_role | count |
|---|---:|
| BACKGROUND | 6 |
| METHOD | 5 |
| RESULT | 5 |
| DEFINE | 4 |
| CLAIM | 3 |
| EXAMPLE | 3 |
| NEXT_STEP | 3 |
| LIMITATION | 2 |

## Count By Rubric Issue

| rubric_issue | count |
|---|---:|
| NONE | 8 |
| METHOD_EXAMPLE_BOUNDARY | 5 |
| RESULT_CLAIM_BOUNDARY | 5 |
| CLAIM_DEFINE_BOUNDARY | 4 |
| BACKGROUND_CLAIM_BOUNDARY | 3 |
| NEXT_STEP_METHOD_BOUNDARY | 3 |
| MULTIWAY_AMBIGUOUS | 2 |
| LIMITATION_CLAIM_BOUNDARY | 1 |

## Rows Where Gold Role Changed

| segment_id | gold_role | adjudicated_role | reason |
|---|---|---|---|
| none |  |  |  |

## Rows Needing Second Review

| segment_id | gold_role | adjudicated_role | status | reason |
|---|---|---|---|---|
| HELDOUT2_S0067 | NEXT_STEP | NEXT_STEP | NEEDS_SECOND_REVIEW | Could read as current instruction, but row proposes a future evaluation question. |