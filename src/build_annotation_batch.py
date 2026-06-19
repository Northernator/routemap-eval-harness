import argparse
from pathlib import Path
import pandas as pd
from common import read_text, split_segments


COLUMNS = [
    "doc_id",
    "segment_id",
    "title",
    "segment_index",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "notes",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-segments-per-doc", type=int, default=80)
    args = ap.parse_args()

    rows = []
    docs = sorted(Path(args.docs).glob("*.txt")) + sorted(Path(args.docs).glob("*.md"))
    for doc_i, path in enumerate(docs, 1):
        text = read_text(path)
        doc_id = f"DOC{doc_i:04d}"
        for j, segment in enumerate(split_segments(text)[:args.max_segments_per_doc]):
            rows.append({
                "doc_id": doc_id,
                "segment_id": f"{doc_id}_S{j+1:04d}",
                "title": path.name,
                "segment_index": j,
                "text": segment,
                "gold_role": "",
                "gold_entities": "",
                "gold_operative_status": "",
                "gold_relation": "",
                "gold_answer_relevant": "",
                "notes": "",
            })

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=COLUMNS).to_csv(args.out, index=False)
    print(f"Wrote {len(rows)} annotation rows to {args.out}")


if __name__ == "__main__":
    main()
