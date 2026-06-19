import argparse, json
from pathlib import Path
import pandas as pd
import numpy as np
from common import token_overlap_score, reciprocal_rank

RESULT_COLUMNS = ["query_id", "method", "hit", "mrr", "comparisons"]

def run_keyword(segments, queries, topk=10):
    rows = []
    for _, q in queries.iterrows():
        doc_segments = segments[segments.doc_id == q.target_doc_id]
        scored = []
        for _, s in doc_segments.iterrows():
            scored.append((s.segment_id, token_overlap_score(q["query"], s.text)))
        ranked = [sid for sid, _ in sorted(scored, key=lambda x: x[1], reverse=True)[:topk]]
        required = str(q.gold_required_segment_ids).split("|")
        hit = any(x in ranked for x in required)
        rr = max([reciprocal_rank(ranked, x) for x in required] or [0])
        rows.append({"query_id": q.query_id, "method": "keyword", "hit": float(hit), "mrr": rr, "comparisons": len(doc_segments)})
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold-segments", required=True)
    ap.add_argument("--gold-qa", required=True)
    ap.add_argument("--out", default="data/outputs/baseline_results.csv")
    args = ap.parse_args()

    segments = pd.read_csv(args.gold_segments)
    queries = pd.read_csv(args.gold_qa)
    res = run_keyword(segments, queries)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(args.out, index=False)
    if res.empty:
        print(f"No QA rows to score. Wrote empty results to {args.out}")
    else:
        print(res.groupby("method").agg(hit=("hit","mean"), mrr=("mrr","mean"), comparisons=("comparisons","mean")))

if __name__ == "__main__":
    main()
