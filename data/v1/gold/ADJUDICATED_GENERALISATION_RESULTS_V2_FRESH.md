# Adjudicated Generalisation Results v2 Fresh

## Adjudication Summary

| item | count |
|---|---:|
| Total rows | 80 |
| Included rows | 79 |
| Excluded rows | 1 |
| ACCEPT_GOLD | 79 |
| CHANGE_GOLD | 0 |
| NEEDS_SECOND_REVIEW | 1 |
| RUBRIC_AMBIGUOUS | 0 |

One row remains excluded pending second review. No original gold files were modified, and no corrected gold file was created.

## Role Baseline Comparison

| baseline | adjudicated role accuracy |
|---|---:|
| Rule v2 | 0.329 |
| Naive Bayes | 0.430 |
| Hybrid NB/rules | 0.418 |

Best role baseline: Naive Bayes.

Mismatch files:

- Rule v2: `data/v1/gold/adjudicated_role_mismatches_rule_v2_fresh.csv`
- Naive Bayes: `data/v1/gold/adjudicated_role_mismatches_nb_v2_fresh.csv`
- Hybrid NB/rules: `data/v1/gold/adjudicated_role_mismatches_hybrid_v2_fresh.csv`

## Full Extraction Metrics

| metric | score |
|---|---:|
| Role accuracy | 0.329 |
| Operative status accuracy | 0.494 |
| Relation accuracy | 0.316 |
| Answer relevance accuracy | 0.886 |
| Entity exact match | 0.013 |
| Entity average Jaccard | 0.283 |
| Strict full-row accuracy | 0.000 |

Full-extraction mismatch file: `data/v1/gold/adjudicated_full_extraction_mismatches_v2_fresh.csv`

## Interpretation

Adjudication did not materially change the earlier conclusion. The fresh held-out v2 labels mostly held up: 79 rows were accepted as gold, no rows were marked as change candidates, and one row remains excluded pending second review.

The main bottleneck remains role generalisation for the rule-based extractor, with entity extraction also a severe bottleneck for full-row accuracy. Naive Bayes remains the strongest role baseline on adjudicated labels, but its accuracy is still low at 0.430, so this is evidence for exploring trained baselines rather than evidence of a robust classifier.

Because strict full-row accuracy remains 0.000 and entity average Jaccard remains 0.283, full extraction still needs both better role modelling and a broader, less brittle entity recognizer.
