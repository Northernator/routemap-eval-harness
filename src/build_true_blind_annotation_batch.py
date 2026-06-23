import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRUE_BLIND_ROOT = ROOT / "data/v1/true_blind_natural_language"
RAW_DOCS = TRUE_BLIND_ROOT / "raw_docs"
ANNOTATION_DIR = TRUE_BLIND_ROOT / "annotation"
PREDICTIONS_DIR = TRUE_BLIND_ROOT / "predictions"
REPORTS_DIR = TRUE_BLIND_ROOT / "reports"
AUDITS_DIR = TRUE_BLIND_ROOT / "audits"
INPUT_README = TRUE_BLIND_ROOT / "TRUE_BLIND_INPUT_README.md"
OUT_CSV = ANNOTATION_DIR / "true_blind_annotation_batch.csv"

README_TEXT = """# True-Blind Natural-Language Input README

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
"""

COLUMNS = [
    "doc_id",
    "segment_id",
    "source_doc",
    "title",
    "segment_index",
    "context_before",
    "segment_text",
    "text",
    "context_after",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "notes",
]


def ensure_dirs():
    for path in [TRUE_BLIND_ROOT, RAW_DOCS, ANNOTATION_DIR, PREDICTIONS_DIR, REPORTS_DIR, AUDITS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def raw_doc_paths():
    return sorted(RAW_DOCS.glob("*.md")) + sorted(RAW_DOCS.glob("*.txt"))


def normalize_ws(value):
    return re.sub(r"\s+", " ", value).strip()


def split_segments(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [normalize_ws(block) for block in re.split(r"\n\s*\n+", text) if normalize_ws(block)]
    segments = []
    for block in blocks:
        if len(block.split()) <= 110:
            segments.append(block)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", block)
        current = []
        for sentence in sentences:
            candidate = normalize_ws(" ".join([*current, sentence]))
            if current and len(candidate.split()) > 90:
                segments.append(normalize_ws(" ".join(current)))
                current = [sentence]
            else:
                current.append(sentence)
        if current:
            segments.append(normalize_ws(" ".join(current)))
    return [segment for segment in segments if len(segment.split()) >= 8]


def build_rows(paths):
    rows = []
    next_segment = 1
    for doc_index, path in enumerate(paths, start=1):
        text = path.read_text(encoding="utf-8-sig")
        segments = split_segments(text)
        doc_id = f"TBDOC{doc_index:03d}"
        for segment_index, segment in enumerate(segments):
            segment_id = f"TB{next_segment:03d}"
            rows.append({
                "doc_id": doc_id,
                "segment_id": segment_id,
                "source_doc": path.name,
                "title": path.name,
                "segment_index": segment_index,
                "context_before": segments[segment_index - 1] if segment_index else "",
                "segment_text": segment,
                "text": segment,
                "context_after": segments[segment_index + 1] if segment_index + 1 < len(segments) else "",
                "gold_role": "",
                "gold_entities": "",
                "gold_operative_status": "",
                "gold_relation": "",
                "gold_answer_relevant": "",
                "notes": "",
            })
            next_segment += 1
    return rows


def write_rows(rows):
    if not rows:
        raise ValueError("No annotation segments were produced from raw docs.")
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    ensure_dirs()
    docs = raw_doc_paths()
    print(f"raw_docs_found={len(docs)}")
    if not docs:
        INPUT_README.write_text(README_TEXT, encoding="utf-8")
        print(f"annotation_batch_path={OUT_CSV.relative_to(ROOT)}")
        print("gold_validation_result=not_run_missing_human_gold")
        print("Add new blind raw docs, then rerun this script.")
        return
    rows = build_rows(docs)
    write_rows(rows)
    print(f"annotation_batch_path={OUT_CSV.relative_to(ROOT)}")
    print(f"annotation_rows={len(rows)}")
    print("gold_validation_result=not_run_missing_human_gold")
    print("Fill true_blind_gold.csv manually, then run validate_true_blind_gold.py.")


if __name__ == "__main__":
    main()
