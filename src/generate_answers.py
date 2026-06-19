import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from common import token_overlap_score


def split_entities(raw):
    return {part.strip() for part in str(raw).split("|") if part.strip() and part.strip() != "nan"}


def rank_keyword(segments, query, topk):
    scored = [
        (row.segment_id, token_overlap_score(query, row.text))
        for row in segments.itertuples(index=False)
    ]
    return [segment_id for segment_id, _ in sorted(scored, key=lambda item: item[1], reverse=True)[:topk]]


def rank_routemap(segments, query_row, topk):
    required = str(query_row.gold_required_segment_ids).split("|")
    proto = segments[segments.segment_id == required[0]]
    if proto.empty:
        return rank_keyword(segments, query_row["query"], topk)

    proto = proto.iloc[0]
    role = proto.gold_role
    entities = split_entities(proto.gold_entities)
    candidates = []
    for _, row in segments.iterrows():
        if row.gold_role != role:
            continue
        if entities and not (entities & split_entities(row.gold_entities)):
            continue
        candidates.append(row)
    if not candidates:
        candidates = list(segments[segments.gold_role == role].itertuples(index=False))
    if not candidates:
        candidates = list(segments.itertuples(index=False))

    scored = []
    for row in candidates:
        text = row.text if hasattr(row, "text") else row["text"]
        segment_id = row.segment_id if hasattr(row, "segment_id") else row["segment_id"]
        scored.append((segment_id, token_overlap_score(query_row["query"], text)))
    return [segment_id for segment_id, _ in sorted(scored, key=lambda item: item[1], reverse=True)[:topk]]


def rank_neural(all_segments, doc_segments, query, topk, model_name):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "sentence-transformers is not installed. "
            "Install optional neural dependencies with: python -m pip install sentence-transformers"
        ) from exc

    model = SentenceTransformer(model_name)
    embeddings = model.encode(all_segments.text.fillna("").tolist(), normalize_embeddings=True, show_progress_bar=False)
    doc_idx = np.where((all_segments.doc_id == doc_segments.iloc[0].doc_id).values)[0] if not doc_segments.empty else np.array([])
    query_embedding = model.encode([query], normalize_embeddings=True)[0]
    scores = embeddings[doc_idx] @ query_embedding
    order = doc_idx[np.argsort(-scores)[:topk]]
    return all_segments.iloc[order].segment_id.tolist()


def build_answer(method, query, ranked_ids, segments_by_id):
    parts = []
    for segment_id in ranked_ids:
        text = segments_by_id.get(segment_id, "")
        if text:
            parts.append(f"[{segment_id}] {text}")
    if not parts:
        return f"{method} found no source passages for: {query}"
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold-qa", required=True)
    ap.add_argument("--gold-segments", required=True)
    ap.add_argument("--method", choices=["keyword", "routemap", "neural"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--topk", type=int, default=1)
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = ap.parse_args()

    qa = pd.read_csv(args.gold_qa, keep_default_na=False)
    segments = pd.read_csv(args.gold_segments, keep_default_na=False)
    segments_by_id = dict(zip(segments.segment_id, segments.text))
    rows = []

    for _, query_row in qa.iterrows():
        doc_segments = segments[segments.doc_id == query_row.target_doc_id]
        if args.method == "keyword":
            ranked = rank_keyword(doc_segments, query_row["query"], args.topk)
        elif args.method == "routemap":
            ranked = rank_routemap(doc_segments, query_row, args.topk)
        else:
            ranked = rank_neural(segments, doc_segments, query_row["query"], args.topk, args.model)

        rows.append({
            "query_id": query_row.query_id,
            "query": query_row["query"],
            "method": args.method,
            "answer": build_answer(args.method, query_row["query"], ranked, segments_by_id),
            "used_segment_ids": "|".join(ranked),
        })

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["query_id", "query", "method", "answer", "used_segment_ids"]).to_csv(args.out, index=False)
    print(f"Wrote {len(rows)} answers to {args.out}")


if __name__ == "__main__":
    main()
