# Boundary Pair Dataset Card v1

## Why This Dataset Exists

The fresh adjudicated RouteMap v2 test showed that coarse route-function signal is real, but exact 8-role classification remains brittle. This boundary-pair dataset targets the hardest role distinctions directly so future models can learn fine-grained role boundaries without tuning on the locked fresh adjudicated test set.

## Boundary Pairs Covered

- CLAIM vs DEFINE
- RESULT vs CLAIM
- BACKGROUND vs CLAIM
- BACKGROUND vs EXAMPLE
- BACKGROUND vs RESULT
- METHOD vs EXAMPLE
- RESULT vs METHOD
- CLAIM vs METHOD

## Row Counts

- Total rows: 200
- Rows per boundary pair: 25
- Target split: 60% train, 20% dev, 20% test

## Label Balance

Each boundary pair has 12 or 13 rows per side. Overall label counts are intentionally concentrated around the hard fine-role boundaries rather than the full role distribution.

## Difficulty Distribution

Rows are mostly MEDIUM and HARD by design. They include definitions that sound like claims, claims with definition-like nouns, procedural examples, result-like methods, and background rows with substantive keywords.

## Intended Use

- Use `boundary_pair_train_v1.csv`, `boundary_pair_dev_v1.csv`, and `boundary_pair_test_v1.csv` for boundary role discrimination experiments.
- Use the train/dev split for model and prompt iteration.
- Use the test split only for final boundary-pair evaluation.
- This dataset is not a replacement for the fresh adjudicated generalisation test.

## What Should Not Be Claimed

- Do not claim full RouteMap extraction is solved from this dataset alone.
- Do not tune on `boundary_pair_test_v1.csv`.
- Do not use boundary-pair gains as evidence that entity extraction is solved.

## Next Recommended Step

If boundary training improves boundary-pair test accuracy, expand this dataset to 500+ rows with broader source styles and more adversarial examples. If it does not help, test stronger classifiers or LLM-based route labelling with the same train/dev/test discipline.
