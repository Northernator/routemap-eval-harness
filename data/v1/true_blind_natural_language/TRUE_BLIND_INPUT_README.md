# True-Blind Natural-Language Input README

Add new blind raw documents here:

`data/v1/true_blind_natural_language/raw_docs/`

Required input:

- 5 to 10 new natural-language route-note documents.
- Preferably 150-500 words each.
- Use `.md` or `.txt`.
- Content must not be copied from old RouteMap docs.
- Content must not be copied from previous annotation, gold, calibration, dev, or test files.

Acceptable sources:

- Fresh notes written by you.
- Newly drafted project descriptions.
- Unseen public-domain technical paragraphs manually pasted in.
- New route-style notes about other projects.

Unacceptable sources:

- `v1_full_extraction_gold_v1_noleak.csv`
- `expanded_test_v2.csv`
- `HELDOUT2` rows.
- Any prior calibration, dev, or test files.

After adding raw docs, run:

```powershell
python src/build_true_blind_annotation_batch.py
```

Then fill labels manually and save completed human annotation as:

`data/v1/true_blind_natural_language/annotation/true_blind_gold.csv`
