# Fresh Held-Out v2 Full Extraction Results

## Dataset

- Source role file: `data/v1/gold/heldout_role_eval_v2.csv`
- Fresh full gold: `data/v1/gold/heldout_full_extraction_gold_v2.csv`
- Fresh v2 prediction: `data/v1/gold/heldout_full_extraction_pred_v2_fresh.csv`
- Dataset size: 80 rows
- Role balance: 10 rows for each role

| role | rows |
|---|---:|
| BACKGROUND | 10 |
| CLAIM | 10 |
| DEFINE | 10 |
| METHOD | 10 |
| RESULT | 10 |
| LIMITATION | 10 |
| NEXT_STEP | 10 |
| EXAMPLE | 10 |

## Scores

| metric | score |
|---|---:|
| Role accuracy | 0.325 |
| Operative status accuracy | 0.500 |
| Relation accuracy | 0.312 |
| Answer relevance accuracy | 0.887 |
| Entity exact match | 0.013 |
| Entity average Jaccard | 0.284 |
| Strict full-row accuracy | 0.000 |

## Mismatches

- Strict mismatch count: 80
- Mismatch review file: `data/v1/gold/heldout_full_extraction_mismatches_v2_fresh.csv`
- Error analysis: `data/v1/gold/HELDOUT_FULL_EXTRACTION_ERROR_ANALYSIS_V2_FRESH.md`
- Error detail CSV: `data/v1/gold/heldout_full_extraction_error_analysis_v2_fresh.csv`
- Rows with zero entity overlap: 17

Field mismatch counts:

| field | mismatches |
|---|---:|
| role | 54 |
| operative_status | 40 |
| relation | 55 |
| answer_relevant | 9 |

## Top Role Confusions

| gold_role | pred_role | count |
|---|---|---:|
| BACKGROUND | CLAIM | 8 |
| DEFINE | CLAIM | 8 |
| EXAMPLE | CLAIM | 8 |
| METHOD | CLAIM | 8 |
| RESULT | CLAIM | 5 |
| NEXT_STEP | CLAIM | 4 |
| LIMITATION | CLAIM | 3 |
| RESULT | METHOD | 3 |
| CLAIM | LIMITATION | 2 |
| CLAIM | METHOD | 1 |

## Top Missing Entities

| entity | count |
|---|---:|
| evidence selection | 24 |
| route segment | 15 |
| model release governance | 14 |
| audit trail | 11 |
| answer support | 10 |
| tool-use security | 9 |
| consent boundary | 8 |
| source context | 8 |
| human review | 8 |
| policy context | 7 |

## Top Failure Patterns

| failure_pattern | count |
|---|---:|
| role+operative_status+relation+entity | 32 |
| entity | 24 |
| role+relation+entity | 14 |
| role+operative_status+relation+answer_relevant+entity | 7 |
| role+operative_status+relation+answer_relevant | 1 |
| answer_relevant+entity | 1 |
| relation+entity | 1 |

## Interpretation

This is the first fresh generalisation test after tuning v2 on the earlier held-out development set. Performance drops substantially from the tuned development-set result, especially on role, relation, entity exact match, and strict full-row accuracy. That drop is evidence that the v2 extractor is development-set overfit and still depends heavily on surface wording from the prior held-out analysis.

The strongest remaining failure mode is renewed `CLAIM` overprediction on fresh background, definition, method, result, next-step, and example wording. Entity extraction also misses fresh canonical concepts such as `evidence selection`, `model release governance`, `audit trail`, and `answer support`. Future improvements should be developed against a separate development split and then measured again on a locked fresh test split.
