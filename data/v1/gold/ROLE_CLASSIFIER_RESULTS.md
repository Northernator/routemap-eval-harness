# RouteMap v1 Role Classifier Results

## Dataset

- Documents: 10
- Annotation rows: 99
- Labels: BACKGROUND, CLAIM, DEFINE, METHOD, RESULT, LIMITATION, NEXT_STEP, EXAMPLE

## Results

| Classifier | Test Type | Accuracy | Notes |
|---|---:|---:|---|
| sample_role | original generated labels | 0.414 | Over-predicts CLAIM and METHOD |
| pred_role_v2 | heading-aware | 1.000 | Inflated by explicit headings |
| pred_role_v2_noleak | headings stripped | 0.525 | Honest semantic baseline |
| pred_role_v3_noleak | headings stripped | 1.000 | Rule-tuned to v1 seed set |

## Interpretation

The v3 classifier proves that role routing can be made deterministic on the seed corpus, but the result is likely overfit because the rules were written from the mismatch examples. The next validation step is a held-out no-leak dataset with new passages and no explicit role headings.
