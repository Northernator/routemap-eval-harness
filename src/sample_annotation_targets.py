import argparse
from pathlib import Path
import pandas as pd


TARGET_ROLES = [
    "DEFINE",
    "CLAIM",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
    "BACKGROUND",
]


def clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def infer_role(text):
    lowered = str(text).lower()
    if any(token in lowered for token in ["defined as", "refers to", "means", "is defined"]):
        return "DEFINE"
    if any(token in lowered for token in ["method", "computes", "procedure", "algorithm"]):
        return "METHOD"
    if any(token in lowered for token in ["result", "shows", "found", "reports"]):
        return "RESULT"
    if any(token in lowered for token in ["limitation", "caveat", "rather than"]):
        return "LIMITATION"
    if any(token in lowered for token in ["next step", "future", "test human"]):
        return "NEXT_STEP"
    if any(token in lowered for token in ["for example", "illustration", "illustrative"]):
        return "EXAMPLE"
    if any(token in lowered for token in ["background", "previous drafts", "not in force"]):
        return "BACKGROUND"
    return "CLAIM"


def role_for_row(row):
    for column in ["gold_role", "llm_role", "predicted_role"]:
        if column in row and clean(row[column]):
            return clean(row[column])
    return infer_role(row.get("text", ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-per-role", type=int, default=50)
    args = ap.parse_args()

    df = pd.read_csv(args.gold, keep_default_na=False)
    df["sample_role"] = df.apply(role_for_row, axis=1)
    rows = []
    for role in TARGET_ROLES:
        role_rows = df[df.sample_role == role].sort_values(["doc_id", "segment_index"]).head(args.max_per_role)
        rows.append(role_rows)

    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=list(df.columns))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out)} annotation targets to {args.out}")
    print(out.groupby("sample_role").size().to_string() if not out.empty else "No annotation targets")


if __name__ == "__main__":
    main()
