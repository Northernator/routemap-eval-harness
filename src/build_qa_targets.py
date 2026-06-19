import argparse
from pathlib import Path
import pandas as pd


COLUMNS = [
    "query_id",
    "doc_id",
    "target_role",
    "candidate_segment_ids",
    "candidate_text",
    "query",
    "gold_required_segment_ids",
    "gold_answer",
    "notes",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold-segments", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-per-role", type=int, default=50)
    args = ap.parse_args()

    segments = pd.read_csv(args.gold_segments, keep_default_na=False)
    rows = []
    for role, group in segments.groupby("gold_role", sort=True):
        if not role:
            continue
        for _, row in group.sort_values(["doc_id", "segment_index"]).head(args.max_per_role).iterrows():
            rows.append({
                "query_id": f"V1_Q{len(rows) + 1:04d}",
                "doc_id": row.doc_id,
                "target_role": role,
                "candidate_segment_ids": row.segment_id,
                "candidate_text": row.text,
                "query": "",
                "gold_required_segment_ids": "",
                "gold_answer": "",
                "notes": "",
            })

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=COLUMNS).to_csv(args.out, index=False)
    print(f"Wrote {len(rows)} QA targets to {args.out}")


if __name__ == "__main__":
    main()
