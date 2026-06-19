import argparse
from pathlib import Path
import pandas as pd
from common import read_text, split_segments

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-segments-per-doc", type=int, default=80)
    args = ap.parse_args()

    rows = []
    docs = list(Path(args.docs).glob("*.txt")) + list(Path(args.docs).glob("*.md"))
    for doc_i, path in enumerate(docs, 1):
        text = read_text(path)
        segs = split_segments(text)
        doc_id = f"DOC{doc_i:04d}"
        for j, seg in enumerate(segs[:args.max_segments_per_doc]):
            rows.append({
                "doc_id": doc_id,
                "segment_id": f"{doc_id}_S{j+1:04d}",
                "title": path.name,
                "segment_index": j,
                "text": seg,
                "gold_role": "",
                "gold_entities": "",
                "gold_operative_status": "",
                "gold_relation": "",
                "gold_answer_relevant": "",
                "notes": ""
            })
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"Wrote {len(rows)} rows to {args.out}")

if __name__ == "__main__":
    main()