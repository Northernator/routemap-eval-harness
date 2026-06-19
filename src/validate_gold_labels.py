import argparse
import json
from pathlib import Path
import pandas as pd
from annotation_summary import summary_text


REQUIRED_COLUMNS = [
    "doc_id",
    "segment_id",
    "title",
    "segment_index",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "notes",
]

REQUIRED_LABELS = [
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
]


def project_root():
    return Path(__file__).resolve().parents[1]


def load_schema(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def normalized(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def validate(gold_path, schema_path):
    schema = load_schema(schema_path)
    df = pd.read_csv(gold_path, keep_default_na=False)
    errors = []

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    for column in missing_columns:
        errors.append(f"missing required column: {column}")
    if missing_columns:
        return errors

    valid_roles = set(schema["roles"])
    valid_statuses = set(schema["operative_status"])
    valid_relations = set(schema["relations"])
    valid_answer_relevant = {"0", "1", "yes", "no", "true", "false"}

    for row_number, row in df.iterrows():
        label = f"row {row_number + 2} segment {row['segment_id']}"
        for column in REQUIRED_LABELS:
            if normalized(row[column]) == "":
                errors.append(f"{label}: empty required label {column}")

        role = normalized(row["gold_role"])
        status = normalized(row["gold_operative_status"])
        relation = normalized(row["gold_relation"])
        answer_relevant = normalized(row["gold_answer_relevant"]).lower()

        if role and role not in valid_roles:
            errors.append(f"{label}: invalid gold_role '{role}'")
        if status and status not in valid_statuses:
            errors.append(f"{label}: invalid gold_operative_status '{status}'")
        if relation and relation not in valid_relations:
            errors.append(f"{label}: invalid gold_relation '{relation}'")
        if answer_relevant and answer_relevant not in valid_answer_relevant:
            errors.append(f"{label}: invalid gold_answer_relevant '{row['gold_answer_relevant']}'")

    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--schema", default=str(project_root() / "configs" / "route_schema.json"))
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()

    errors = validate(args.gold, args.schema)
    if errors:
        print(f"Validation failed: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Validation passed: {args.gold}")
    if args.summary:
        print()
        print(summary_text(Path(args.gold)))


if __name__ == "__main__":
    main()
