# Annotation Workflow

Generate a cleaner manual-annotation CSV from the sampled v1 targets:

```powershell
python src/make_clean_annotation_csv.py --in data/v1/gold/v1_annotation_targets.csv --out data/v1/gold/v1_annotation_targets_clean.csv
```

Open `data/v1/gold/v1_annotation_targets_clean.csv` in Excel, LibreOffice Calc, Google Sheets, or another CSV editor that preserves UTF-8 CSV quoting and multiline cells.

Edit these columns first:

1. `gold_role`
2. `gold_entities`
3. `gold_operative_status`
4. `gold_relation`
5. `gold_answer_relevant`
6. `notes`

Use `sample_role` as a hint only. Do not edit `doc_id`, `segment_id`, `title`, `segment_index`, or `text` unless fixing a known source issue.

Allowed `gold_role` labels:

- `BACKGROUND`
- `CLAIM`
- `DEFINE`
- `METHOD`
- `RESULT`
- `LIMITATION`
- `NEXT_STEP`
- `EXAMPLE`

Validate after editing:

```powershell
python src/validate_annotation_csv.py --csv data/v1/gold/v1_annotation_targets_clean.csv
```
