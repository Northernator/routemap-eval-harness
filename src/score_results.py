import argparse
from pathlib import Path
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs", required=True)
    args = ap.parse_args()

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
