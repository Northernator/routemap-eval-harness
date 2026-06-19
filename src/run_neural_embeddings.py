"""
Optional modern neural embedding baseline.

Requires:
    pip install sentence-transformers

Example:
    python src/run_neural_embeddings.py --gold-segments data/gold/gold_segments_filled.csv --gold-qa data/gold/gold_qa_filled.csv

Default model can be changed with --model.
"""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from common import reciprocal_rank

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold-segments", required=True)
    ap.add_argument("--gold-qa", required=True)
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--out", default="data/outputs/neural_embedding_results.csv")
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(args.model)

    seg = pd.read_csv(args.gold_segments)
    qa = pd.read_csv(args.gold_qa)
    emb = model.encode(seg.text.fillna("").tolist(), normalize_embeddings=True, show_progress_bar=True)

    rows = []
    for _, q in qa.iterrows():
        doc_mask = seg.doc_id == q.target_doc_id
        doc_idx = np.where(doc_mask.values)[0]
        q_emb = model.encode([q["query"]], normalize_embeddings=True)[0]
        scores = emb[doc_idx] @ q_emb
        order = doc_idx[np.argsort(-scores)[:10]]
        ranked = seg.iloc[order].segment_id.tolist()
        required = str(q.gold_required_segment_ids).split("|")
        hit = any(x in ranked for x in required)
        rr = max([reciprocal_rank(ranked, x) for x in required] or [0])
        rows.append({"query_id": q.query_id, "method": "neural_embedding", "hit": float(hit), "mrr": rr, "comparisons": len(doc_idx)})

    out = pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(out.groupby("method").agg(hit=("hit","mean"), mrr=("mrr","mean"), comparisons=("comparisons","mean")))

if __name__ == "__main__":
    main()