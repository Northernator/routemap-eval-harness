import argparse
from pathlib import Path
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True, help="CSV with query_id, answer, used_segment_ids")
    ap.add_argument("--gold-qa", required=True)
    ap.add_argument("--out", default="data/outputs/qa_eval_results.csv")
    args = ap.parse_args()

    answers = pd.read_csv(args.answers)
    gold = pd.read_csv(args.gold_qa)

    rows = []
    for _, a in answers.iterrows():
        g = gold[gold.query_id == a.query_id]
        if g.empty:
            continue
        g = g.iloc[0]
        required = set(str(g.gold_required_segment_ids).split("|"))
        used = set(str(a.used_segment_ids).split("|"))
        source_hit = len(required & used) > 0
        all_sources = required.issubset(used)
        rows.append({
            "query_id": a.query_id,
            "source_hit": float(source_hit),
            "all_required_sources_used": float(all_sources),
        })

    out = pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(out.mean(numeric_only=True))

if __name__ == "__main__":
    main()