import argparse
from pathlib import Path
import pandas as pd


METRIC_COLUMNS = ["method", "hit", "mrr", "comparisons", "comparison_reduction_pct"]


def summarize_method_outputs(output_dir):
    frames = []
    for path in Path(output_dir).glob("*results.csv"):
        df = pd.read_csv(path)
        if "method" not in df.columns or df.empty:
            continue
        for column in METRIC_COLUMNS:
            if column not in df.columns:
                df[column] = 0.0
        frames.append(df[METRIC_COLUMNS])
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    summary = combined.groupby("method", as_index=False).agg(
        **{
            "Hit@K": ("hit", "mean"),
            "MRR": ("mrr", "mean"),
            "comparisons/query": ("comparisons", "mean"),
            "comparison reduction %": ("comparison_reduction_pct", "mean"),
        }
    )
    return summary.sort_values(["Hit@K", "MRR", "comparison reduction %"], ascending=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs", required=True)
    args = ap.parse_args()

    summary = summarize_method_outputs(args.outputs)
    if not summary.empty:
        print("\n== keyword vs RouteMap vs neural embeddings ==")
        print(summary.to_string(index=False))

    for path in Path(args.outputs).glob("*.csv"):
        df = pd.read_csv(path)
        print("\\n==", path.name, "==")
        numeric = df.select_dtypes("number")
        if "method" in df.columns:
            print(df.groupby("method").mean(numeric_only=True))
        elif {"source_hit", "all_required_sources_used"} & set(df.columns):
            print(df.mean(numeric_only=True))
        elif not numeric.empty:
            print("No score columns found; skipped metric summary.")
        else:
            print("No score columns found; skipped metric summary.")

if __name__ == "__main__":
    main()
