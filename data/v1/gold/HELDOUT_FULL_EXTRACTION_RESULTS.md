# Held-Out Full Extraction Results

## Dataset

- Source role file: `data/v1/gold/heldout_role_eval.csv`
- Held-out full gold: `data/v1/gold/heldout_full_extraction_gold_v1.csv`
- Held-out full prediction: `data/v1/gold/heldout_full_extraction_pred_v1.csv`
- Dataset size: 80 rows
- Role balance: 10 rows for each role

## Scores

| metric | score |
|---|---:|
| Role accuracy | 0.450 |
| Operative status accuracy | 0.613 |
| Relation accuracy | 0.438 |
| Answer relevance accuracy | 0.875 |
| Entity exact match | 0.300 |
| Entity average Jaccard | 0.405 |
| Strict full-row accuracy | 0.113 |

## Counts

| role | gold_role | pred_role |
|---|---:|---:|
| BACKGROUND | 10 | 4 |
| CLAIM | 10 | 53 |
| DEFINE | 10 | 2 |
| METHOD | 10 | 4 |
| RESULT | 10 | 1 |
| LIMITATION | 10 | 4 |
| NEXT_STEP | 10 | 5 |
| EXAMPLE | 10 | 7 |

## Mismatches

- Strict mismatch count: 71
- Mismatch review file: `data/v1/gold/heldout_full_extraction_mismatches_v1.csv`
- Rows with zero entity overlap: 33

Field mismatch counts:

| field | mismatches |
|---|---:|
| role | 44 |
| operative_status | 31 |
| relation | 45 |
| answer_relevant | 10 |

## Interpretation

This is the first held-out full RouteMap extraction test, and it should be treated as more meaningful than the seed 1.000 scores. The low strict full-row accuracy is useful: it shows that the full route annotation structure does not yet generalise beyond the seed wording and heading-friendly corpus.

The largest failure mode is role overprediction of `CLAIM`, which then propagates into relation and operative-status errors. Entity extraction also drops sharply because held-out gold entities were annotated by a separate script rather than copied from the prediction heuristic.

Next work should target broader semantic role coverage, independent entity extraction, and a manually adjudicated subset for relation and operative-status labels.

## v2 Tuned Development-Set Extractor

Files:

- Held-out full prediction: `data/v1/gold/heldout_full_extraction_pred_v2.csv`
- Mismatch review file: `data/v1/gold/heldout_full_extraction_mismatches_v2.csv`
- Error analysis: `data/v1/gold/HELDOUT_FULL_EXTRACTION_ERROR_ANALYSIS_V2.md`
- Error detail CSV: `data/v1/gold/heldout_full_extraction_error_analysis_v2.csv`

The v2 extractor uses `src/role_classifier_v4.py`, `src/entity_extractor_v2.py`, and `src/predict_heldout_full_extraction_v2.py`. It is tuned from the v1 held-out error analysis, so these scores should be treated as development-set performance, not final generalisation evidence.

| metric | v1 held-out | v2 tuned dev-set | delta |
|---|---:|---:|---:|
| Role accuracy | 0.450 | 0.988 | +0.538 |
| Operative status accuracy | 0.613 | 1.000 | +0.387 |
| Relation accuracy | 0.438 | 0.875 | +0.437 |
| Answer relevance accuracy | 0.875 | 1.000 | +0.125 |
| Entity exact match | 0.300 | 0.500 | +0.200 |
| Entity average Jaccard | 0.405 | 0.712 | +0.307 |
| Strict full-row accuracy | 0.113 | 0.475 | +0.362 |

| count | v1 | v2 |
|---|---:|---:|
| Strict mismatch count | 71 | 42 |
| Rows with zero entity overlap | 33 | 7 |
| Role mismatches | 44 | 1 |
| Operative-status mismatches | 31 | 0 |
| Relation mismatches | 45 | 10 |
| Answer-relevance mismatches | 10 | 0 |

The main v2 gain comes from reducing `CLAIM` overprediction by checking background, definition, result, next-step, example, limitation, and method cues before defaulting to `CLAIM`. Remaining errors are mostly entity exact-match misses and relation labels that still use a role-first mapping.

Before making generalisation claims, create a fresh held-out v2 dataset that was not used to design these rules, then rerun prediction, evaluation, and error analysis on that untouched split.
