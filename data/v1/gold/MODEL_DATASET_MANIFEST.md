# Model Dataset Manifest

## Training / Development Allowed

These files may be used for training, feature design, development experiments, and cross-validation:

- `data/v1/gold/v1_full_extraction_gold_v1_noleak.csv`
- `data/v1/gold/heldout_full_extraction_gold_v1.csv`

## Development / Error-Analysis Set

These files were used during v2 rule analysis and should be treated as development data, not final evidence:

- `data/v1/gold/heldout_full_extraction_gold_v1.csv`
- `data/v1/gold/heldout_full_extraction_pred_v2.csv`
- `data/v1/gold/heldout_full_extraction_error_analysis_v2.csv`

## Fresh Adjudicated Test Set

These files define the locked fresh test set after role adjudication:

- `data/v1/gold/heldout_role_eval_v2_adjudicated.csv`
- `data/v1/gold/heldout_full_extraction_gold_v2_adjudicated.csv`
- `data/v1/gold/heldout_full_extraction_pred_v2_fresh_adjudicated.csv`

Important: the fresh adjudicated test set must not be used for tuning, feature selection, threshold selection, prompt iteration, or rule design. Use it only for final evaluation.

## Model-Ready Derived Files

The next modelling phase should use:

- Train/dev: `data/v1/gold/model_train_dev_role.csv`
- Locked fresh test: `data/v1/gold/model_test_fresh_adjudicated_role.csv`

These are derived convenience CSVs. They do not replace the source gold or adjudication files.
