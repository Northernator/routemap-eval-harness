# Role Generalisation Baselines: Fresh Held-Out v2

## Why This Test Exists

The v2 rule extractor performed strongly on the tuned development set but dropped sharply on the fresh held-out v2 dataset. This baseline suite tests whether a simple trained role classifier generalises better than hand-written rules when it is trained only on existing development data and evaluated once on the fresh held-out v2 split.

## Data Boundaries

Training sources:

- `data/v1/gold/v1_full_extraction_gold_v1_noleak.csv`
- `data/v1/gold/heldout_full_extraction_gold_v1.csv`

Test source:

- `data/v1/gold/heldout_full_extraction_gold_v2.csv`

The fresh held-out v2 file is used only for final evaluation. It is not used to train the Naive Bayes model or tune the hybrid threshold.

## Accuracy Summary

| baseline | fresh held-out v2 role accuracy |
|---|---:|
| Rule v2 | 0.325 |
| Naive Bayes | 0.425 |
| Hybrid NB/rules | 0.412 |

Best role baseline: Naive Bayes.

## Baseline Files

- Naive Bayes predictions: `data/v1/gold/heldout_role_nb_pred_v2_fresh.csv`
- Naive Bayes mismatches: `data/v1/gold/heldout_role_nb_mismatches_v2_fresh.csv`
- Hybrid predictions: `data/v1/gold/heldout_role_hybrid_nb_rules_pred_v2_fresh.csv`
- Hybrid mismatches: `data/v1/gold/heldout_role_hybrid_nb_rules_mismatches_v2_fresh.csv`
- Rule-vs-NB comparison: `data/v1/gold/ROLE_BASELINE_COMPARISON_V2_FRESH.md`

## Naive Bayes Per-Role Metrics

| role | precision | recall | F1 | support |
|---|---:|---:|---:|---:|
| BACKGROUND | 0.400 | 0.200 | 0.267 | 10 |
| CLAIM | 0.214 | 0.300 | 0.250 | 10 |
| DEFINE | 0.462 | 0.600 | 0.522 | 10 |
| METHOD | 0.214 | 0.300 | 0.250 | 10 |
| RESULT | 0.600 | 0.300 | 0.400 | 10 |
| LIMITATION | 0.667 | 0.600 | 0.632 | 10 |
| NEXT_STEP | 0.625 | 0.500 | 0.556 | 10 |
| EXAMPLE | 0.500 | 0.600 | 0.545 | 10 |

## Top Remaining Naive Bayes Confusions

| gold_role | pred_role | count |
|---|---|---:|
| CLAIM | DEFINE | 3 |
| DEFINE | CLAIM | 3 |
| METHOD | EXAMPLE | 3 |
| RESULT | CLAIM | 3 |
| BACKGROUND | CLAIM | 2 |
| BACKGROUND | LIMITATION | 2 |
| BACKGROUND | EXAMPLE | 2 |
| CLAIM | METHOD | 2 |
| METHOD | DEFINE | 2 |
| RESULT | METHOD | 2 |

## Interpretation

The Naive Bayes baseline outperforms the tuned v2 rules on the fresh held-out v2 role task, which suggests that some lexical generalisation is possible even with a small standard-library model. The hybrid also beats the rules, but it does not beat Naive Bayes alone because the rule classifier still overpredicts `CLAIM` in many fresh rows and only some of those cases are overridden by the confidence margin.

This is still a small-data result. Training has only 179 rows, and each fresh test role has 10 rows. The baseline is useful for direction, not as final evidence that a bag-of-words classifier is production-ready.

Next recommended step: create a larger development split for trained baselines, keep the fresh v2 set locked, and add cross-validation on development data before testing any improved trained model on a new untouched split.
