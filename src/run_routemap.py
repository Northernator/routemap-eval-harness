import argparse, re
from pathlib import Path
import pandas as pd
from common import token_overlap_score, reciprocal_rank

RESULT_COLUMNS = ["query_id", "method", "hit", "mrr", "comparisons", "comparison_reduction_pct"]

def parse_entities(s):
    return set([x for x in str(s).split("|") if x and x != "nan"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold-segments", required=True)
    ap.add_argument("--gold-qa", required=True)
    ap.add_argument("--out", default="data/outputs/routemap_results.csv")
    args = ap.parse_args()

    seg = pd.read_csv(args.gold_segments)
    qa = pd.read_csv(args.gold_qa)

    rows = []
    for _, q in qa.iterrows():
        required = str(q.gold_required_segment_ids).split("|")
        # Use first required segment as target route prototype if available.
        proto = seg[seg.segment_id == required[0]]
        if proto.empty:
            continue
        proto = proto.iloc[0]
        ents = parse_entities(proto.gold_entities)
        role = proto.gold_role
        doc_id = q.target_doc_id
        doc_segments = seg[seg.doc_id == doc_id]

        candidates = []
        for _, s in doc_segments.iterrows():
            if s.gold_role != role:
                continue
            if ents and not (ents & parse_entities(s.gold_entities)):
                continue
            candidates.append(s)

        if not candidates:
            candidates = list(doc_segments[doc_segments.gold_role == role].itertuples(index=False))

        scored = []
        for s in candidates:
            text = s.text if hasattr(s, "text") else s["text"]
            sid = s.segment_id if hasattr(s, "segment_id") else s["segment_id"]
            scored.append((sid, token_overlap_score(q["query"], text)))

        ranked = [sid for sid, _ in sorted(scored, key=lambda x: x[1], reverse=True)[:10]]
        hit = any(x in ranked for x in required)
        rr = max([reciprocal_rank(ranked, x) for x in required] or [0])
        total = len(doc_segments)
        reduction = 0.0 if total == 0 else (1.0 - (len(candidates) / total)) * 100.0
        rows.append({
            "query_id": q.query_id,
            "method": "routemap_gold_route",
            "hit": float(hit),
            "mrr": rr,
            "comparisons": len(candidates),
            "comparison_reduction_pct": reduction,
        })

    out = pd.DataFrame(rows, columns=RESULT_COLUMNS)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    if out.empty:
        print(f"No routemap rows to score. Wrote empty results to {args.out}")
    else:
        print(out.groupby("method").agg(hit=("hit","mean"), mrr=("mrr","mean"), comparisons=("comparisons","mean"), comparison_reduction_pct=("comparison_reduction_pct","mean")))

if __name__ == "__main__":
    main()
