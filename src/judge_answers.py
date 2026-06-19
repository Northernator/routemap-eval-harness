import argparse
import re
from pathlib import Path
import pandas as pd
from common import toks


SUMMARY_COLUMNS = ["metric", "value"]


def split_ids(raw):
    return {part.strip() for part in str(raw).split("|") if part.strip()}


def content_terms(text):
    return {term for term in toks(text) if len(term) > 2}


def answer_contains_gold_terms(answer, gold_answer):
    gold_terms = content_terms(gold_answer)
    if not gold_terms:
        return True
    answer_terms = content_terms(answer)
    return len(gold_terms & answer_terms) / len(gold_terms) >= 0.5


def hallucination_flag(answer, used_ids):
    cited_ids = set(re.findall(r"\bDOC\d+_S\d+\b", str(answer)))
    return bool(cited_ids - used_ids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True)
    ap.add_argument("--gold-qa", required=True)
    ap.add_argument("--out", default="data/outputs/qa_judgement_scores.csv")
    ap.add_argument("--summary-out", default="data/outputs/qa_judgement_summary.csv")
    args = ap.parse_args()

    answers = pd.read_csv(args.answers, keep_default_na=False)
    gold = pd.read_csv(args.gold_qa, keep_default_na=False)
    rows = []

    for _, answer_row in answers.iterrows():
        match = gold[gold.query_id == answer_row.query_id]
        if match.empty:
            continue
        gold_row = match.iloc[0]
        required = split_ids(gold_row.gold_required_segment_ids)
        used = split_ids(answer_row.used_segment_ids)
        source_hit = bool(required & used)
        all_required = required.issubset(used)
        contains_terms = answer_contains_gold_terms(answer_row.answer, gold_row.gold_answer)
        hallucinated = hallucination_flag(answer_row.answer, used)
        correctness = source_hit and contains_terms and not hallucinated
        completeness = all_required and contains_terms
        rows.append({
            "query_id": answer_row.query_id,
            "method": answer_row.method,
            "source_hit": float(source_hit),
            "all_required_sources_used": float(all_required),
            "answer_contains_gold_terms": float(contains_terms),
            "hallucination_flag_simple": float(hallucinated),
            "correctness_proxy": float(correctness),
            "completeness_proxy": float(completeness),
        })

    scores = pd.DataFrame(rows)
    if scores.empty:
        summary = pd.DataFrame(columns=SUMMARY_COLUMNS)
    else:
        summary = scores.drop(columns=["query_id"]).groupby("method").mean(numeric_only=True).reset_index()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(args.out, index=False)
    summary.to_csv(args.summary_out, index=False)
    print("== QA judgement summary ==")
    print(summary.to_string(index=False))
    print(f"Wrote {args.out}")
    print(f"Wrote {args.summary_out}")


if __name__ == "__main__":
    main()
