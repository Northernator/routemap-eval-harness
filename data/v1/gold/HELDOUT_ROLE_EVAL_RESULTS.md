# Held-Out Role Evaluation Results

## Dataset

- Dataset: `data/v1/gold/heldout_role_eval.csv`
- Size: 80 rows
- Role balance: 10 rows per role
- Text leak check: no explicit `### ROLE` route headings in `text`

## v3 Evaluation

Command:

```powershell
python src/evaluate_role_labels.py --csv data/v1/gold/heldout_role_eval_v3pred.csv --pred-col pred_role_v3
```

- Accuracy: 0.450
- Correct rows: 36 / 80
- Mismatch count: 44
- Mismatch review file: `data/v1/gold/role_label_mismatches_pred_role_v3.csv`

## Counts

| role | gold_role | pred_role_v3 |
|---|---:|---:|
| BACKGROUND | 10 | 4 |
| CLAIM | 10 | 53 |
| DEFINE | 10 | 2 |
| METHOD | 10 | 4 |
| RESULT | 10 | 1 |
| LIMITATION | 10 | 4 |
| NEXT_STEP | 10 | 5 |
| EXAMPLE | 10 | 7 |

## Per-Role Metrics

| role | precision | recall | F1 | tp | fp | fn |
|---|---:|---:|---:|---:|---:|---:|
| BACKGROUND | 1.000 | 0.400 | 0.571 | 4 | 0 | 6 |
| CLAIM | 0.189 | 1.000 | 0.317 | 10 | 43 | 0 |
| DEFINE | 1.000 | 0.200 | 0.333 | 2 | 0 | 8 |
| METHOD | 0.750 | 0.300 | 0.429 | 3 | 1 | 7 |
| RESULT | 1.000 | 0.100 | 0.182 | 1 | 0 | 9 |
| LIMITATION | 1.000 | 0.400 | 0.571 | 4 | 0 | 6 |
| NEXT_STEP | 1.000 | 0.500 | 0.667 | 5 | 0 | 5 |
| EXAMPLE | 1.000 | 0.700 | 0.824 | 7 | 0 | 3 |

## Top Confusion Pairs

| gold_role | pred_role_v3 | count |
|---|---|---:|
| CLAIM | CLAIM | 10 |
| RESULT | CLAIM | 9 |
| DEFINE | CLAIM | 8 |
| METHOD | CLAIM | 7 |
| EXAMPLE | EXAMPLE | 7 |
| LIMITATION | CLAIM | 6 |
| BACKGROUND | CLAIM | 5 |
| NEXT_STEP | CLAIM | 5 |
| NEXT_STEP | NEXT_STEP | 5 |
| BACKGROUND | BACKGROUND | 4 |

## Interpretation

The held-out result shows that v3 does not yet generalise beyond the original 99-row seed set. The seed-set no-leak score of 1.000 was likely inflated by tuning against known mismatch patterns. On new phrasing, v3 strongly overpredicts `CLAIM`, especially for `DEFINE`, `RESULT`, `METHOD`, `BACKGROUND`, and `NEXT_STEP` rows that do not use the exact trigger wording encoded in the rules.

The current v3 rules are useful as a transparent diagnostic baseline, but not as a robust semantic classifier. Next improvements should use this held-out mismatch file to add broader semantic coverage without hard-coding individual held-out rows, or reserve a second held-out split before further tuning.
