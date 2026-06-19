# RouteMap v1.0 Benchmark Run Checklist

Use this checklist to produce the first real human-gold RouteMap benchmark run.

## 1. Prepare Documents

Place benchmark documents in `data/documents/` as `.txt` or `.md` files.

```bash
dir data\documents
```

Optional quick count:

```bash
python -c "from pathlib import Path; p=Path('data/documents'); print(len(list(p.glob('*.txt')) + list(p.glob('*.md'))))"
```

## 2. Build Annotation Batch

```bash
python src/build_annotation_batch.py --docs data/documents --out data/gold/annotation_batch.csv
```

## 3. Sample Balanced Annotation Targets

```bash
python src/sample_annotation_targets.py --gold data/gold/annotation_batch.csv --out data/gold/v1_annotation_targets.csv --max-per-role 50
```

## 4. Fill Human Labels

Copy the sampled targets to a filled working file:

```bash
copy data\gold\v1_annotation_targets.csv data\gold\v1_annotation_targets_filled.csv
```

Humans fill:

```text
gold_role
gold_entities
gold_operative_status
gold_relation
gold_answer_relevant
notes
```

Use:

```text
docs/ANNOTATION_QUICK_REFERENCE.md
data/gold/ANNOTATION_GUIDELINES.md
configs/route_schema.json
```

## 5. Validate Labels

```bash
python src/validate_gold_labels.py --gold data/gold/v1_annotation_targets_filled.csv --summary
```

Optional summary only:

```bash
python src/annotation_summary.py --gold data/gold/v1_annotation_targets_filled.csv
```

## 6. Build QA Targets

```bash
python src/build_qa_targets.py --gold-segments data/gold/v1_annotation_targets_filled.csv --out data/gold/v1_qa_targets.csv
```

## 7. Fill QA Targets

Copy QA targets to a filled working file:

```bash
copy data\gold\v1_qa_targets.csv data\gold\v1_qa_targets_filled.csv
```

Humans fill:

```text
query
gold_required_segment_ids
gold_answer
notes
```

## 8. Validate QA Targets

```bash
python src/validate_qa_targets.py --qa data/gold/v1_qa_targets_filled.csv --gold-segments data/gold/v1_annotation_targets_filled.csv
```

## 9. Run Batch Evaluation

Full local run:

```bash
python src/run_batch_eval.py --documents data/documents --gold-segments data/gold/v1_annotation_targets_filled.csv --gold-qa data/gold/v1_qa_targets_filled.csv --out data/runs
```

Offline-only run without neural embeddings:

```bash
python src/run_batch_eval.py --documents data/documents --gold-segments data/gold/v1_annotation_targets_filled.csv --gold-qa data/gold/v1_qa_targets_filled.csv --out data/runs --disable-neural
```

## 10. Generate Report

The batch runner generates the report automatically. To regenerate it:

```bash
python src/generate_run_report.py --run-dir data/runs/<timestamp>
```

Open:

```text
data/runs/<timestamp>/report.html
```

## 11. Archive Run Folder

Zip the completed run folder:

```bash
powershell Compress-Archive -Path data\runs\<timestamp> -DestinationPath data\runs\<timestamp>.zip -Force
```

## 12. Record Git Commit Hash

```bash
git rev-parse HEAD
```

Confirm `run_manifest.json` contains the same commit hash:

```bash
type data\runs\<timestamp>\run_manifest.json
```

## 13. Write Result Summary

Create a short benchmark note:

```bash
copy data\runs\<timestamp>\run_summary.md data\runs\<timestamp>\result_summary.md
```

Include:

```text
dataset size
methods compared
best retrieval method
comparison reduction
route extraction score
QA judgement summary
known limitations
follow-up actions
```

## Results Thresholds

- Minimum labelled passages: 1,000 validated human-gold passages.
- Minimum QA queries: 150 validated human-written queries.
- Roles covered: DEFINE, CLAIM, METHOD, RESULT, LIMITATION, NEXT_STEP, EXAMPLE, BACKGROUND.
- Minimum examples per covered role: 50 where the corpus supports the role.
- Methods compared: keyword, RouteMap, and neural embeddings when optional dependencies are available.
- Acceptance criteria:
  - Label validation passes with zero errors.
  - QA validation passes with zero errors.
  - Batch evaluation completes.
  - `run_manifest.json`, `run_summary.md`, `report.html`, and chart PNGs exist.
  - RouteMap retrieval is compared on Hit@K, MRR, comparisons/query, and comparison reduction.
  - Result summary records limitations and follow-up actions.
