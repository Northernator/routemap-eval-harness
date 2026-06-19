import argparse
from pathlib import Path
import pandas as pd


ROLES = [
    "DEFINE",
    "CLAIM",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
    "BACKGROUND",
]

LABEL_COLUMNS = [
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
]


def counts(df, column):
    if column not in df.columns:
        return pd.Series(dtype=int)
    values = df[column].fillna("").astype(str).str.strip()
    return values[values != ""].value_counts().sort_index()


def empty_counts(df):
    rows = []
    for column in LABEL_COLUMNS:
        if column not in df.columns:
            rows.append((column, "missing column"))
            continue
        empty = (df[column].fillna("").astype(str).str.strip() == "").sum()
        rows.append((column, int(empty)))
    return rows


def duplicate_segment_ids(df):
    if "segment_id" not in df.columns:
        return []
    duplicated = df[df.segment_id.duplicated(keep=False)]["segment_id"].tolist()
    return sorted(set(duplicated))


def examples_per_role(df, examples):
    if "gold_role" not in df.columns:
        return {}
    result = {}
    for role, group in df.groupby("gold_role", sort=True):
        role = str(role).strip()
        if not role:
            continue
        result[role] = group[["segment_id", "text"]].head(examples).to_dict("records")
    return result


def summary_text(gold_path, target_count=50, examples=2):
    df = pd.read_csv(gold_path, keep_default_na=False)
    lines = [f"Annotation summary: {gold_path}", f"Total rows: {len(df)}", ""]

    lines.append("Role counts:")
    role_counts = counts(df, "gold_role")
    lines.extend([f"- {role}: {count}" for role, count in role_counts.items()] or ["- none"])
    lines.append("")

    lines.append("Operative status counts:")
    status_counts = counts(df, "gold_operative_status")
    lines.extend([f"- {status}: {count}" for status, count in status_counts.items()] or ["- none"])
    lines.append("")

    lines.append("Relation counts:")
    relation_counts = counts(df, "gold_relation")
    lines.extend([f"- {relation}: {count}" for relation, count in relation_counts.items()] or ["- none"])
    lines.append("")

    lines.append("Empty label counts:")
    for column, count in empty_counts(df):
        lines.append(f"- {column}: {count}")
    lines.append("")

    duplicates = duplicate_segment_ids(df)
    lines.append("Duplicate segment ids:")
    lines.extend([f"- {segment_id}" for segment_id in duplicates] or ["- none"])
    lines.append("")

    lines.append(f"Warnings for roles below target count ({target_count}):")
    warnings = []
    for role in ROLES:
        count = int(role_counts.get(role, 0))
        if count < target_count:
            warnings.append(f"- {role}: {count}/{target_count}")
    lines.extend(warnings or ["- none"])
    lines.append("")

    lines.append(f"Examples per role (up to {examples} each):")
    examples_by_role = examples_per_role(df, examples)
    if not examples_by_role:
        lines.append("- none")
    for role, rows in examples_by_role.items():
        lines.append(f"- {role}:")
        for row in rows:
            text = str(row["text"]).replace("\n", " ")
            if len(text) > 140:
                text = text[:137] + "..."
            lines.append(f"  - {row['segment_id']}: {text}")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="data/gold/v1_annotation_targets_filled.csv")
    ap.add_argument("--target-count", type=int, default=50)
    ap.add_argument("--examples", type=int, default=2)
    args = ap.parse_args()

    print(summary_text(Path(args.gold), args.target_count, args.examples))


if __name__ == "__main__":
    main()
