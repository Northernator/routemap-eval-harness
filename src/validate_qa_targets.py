import argparse
from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = [
    "query_id",
    "doc_id",
    "query",
    "gold_required_segment_ids",
    "gold_answer",
    "notes",
]


def split_ids(value):
    return [part.strip() for part in str(value).split("|") if part.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", required=True)
    ap.add_argument("--gold-segments", required=True)
    args = ap.parse_args()

    qa = pd.read_csv(args.qa, keep_default_na=False)
    segments = pd.read_csv(args.gold_segments, keep_default_na=False)
    valid_segment_ids = set(segments.segment_id)
    errors = []

    for column in REQUIRED_COLUMNS:
        if column not in qa.columns:
            errors.append(f"missing required column: {column}")
    if errors:
        print(f"Validation failed: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    seen = set()
    for row_number, row in qa.iterrows():
        label = f"row {row_number + 2} query {row.query_id}"
        if not str(row.query_id).strip():
            errors.append(f"{label}: empty query_id")
        elif row.query_id in seen:
            errors.append(f"{label}: duplicate query_id")
        seen.add(row.query_id)

        for column in ["query", "gold_required_segment_ids", "gold_answer"]:
            if not str(row[column]).strip():
                errors.append(f"{label}: empty {column}")

        required_ids = split_ids(row.gold_required_segment_ids)
        for segment_id in required_ids:
            if segment_id not in valid_segment_ids:
                errors.append(f"{label}: unknown required segment id {segment_id}")

    if errors:
        print(f"Validation failed: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Validation passed: {args.qa}")


if __name__ == "__main__":
    main()
