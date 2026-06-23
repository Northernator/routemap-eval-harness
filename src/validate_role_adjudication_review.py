import argparse
import csv
from collections import Counter
from pathlib import Path


REQUIRED_COLUMNS = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "pred_rule",
    "pred_nb",
    "pred_hybrid",
    "agreement_pattern",
    "needs_review",
    "likely_ambiguity_type",
    "suggested_review_question",
    "notes",
    "adjudicated_role",
    "adjudication_status",
    "adjudication_reason",
    "rubric_issue",
    "review_priority",
]

ALLOWED_ROLES = {
    "",
    "BACKGROUND",
    "CLAIM",
    "DEFINE",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
}

ALLOWED_STATUSES = {
    "",
    "ACCEPT_GOLD",
    "CHANGE_GOLD",
    "NEEDS_SECOND_REVIEW",
    "RUBRIC_AMBIGUOUS",
}

ALLOWED_RUBRIC_ISSUES = {
    "",
    "NONE",
    "CLAIM_DEFINE_BOUNDARY",
    "METHOD_EXAMPLE_BOUNDARY",
    "RESULT_CLAIM_BOUNDARY",
    "BACKGROUND_CLAIM_BOUNDARY",
    "LIMITATION_CLAIM_BOUNDARY",
    "NEXT_STEP_METHOD_BOUNDARY",
    "MULTIWAY_AMBIGUOUS",
}

ALLOWED_PRIORITIES = {"P1", "P2", "P3", "P4"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()

    with Path(args.csv).open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    invalid_rows = []
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing_columns:
        invalid_rows.append(f"missing columns: {', '.join(missing_columns)}")

    for index, row in enumerate(rows, start=2):
        errors = []
        if row.get("adjudicated_role", "") not in ALLOWED_ROLES:
            errors.append(f"invalid adjudicated_role={row.get('adjudicated_role', '')}")
        if row.get("adjudication_status", "") not in ALLOWED_STATUSES:
            errors.append(f"invalid adjudication_status={row.get('adjudication_status', '')}")
        if row.get("rubric_issue", "") not in ALLOWED_RUBRIC_ISSUES:
            errors.append(f"invalid rubric_issue={row.get('rubric_issue', '')}")
        if row.get("review_priority", "") not in ALLOWED_PRIORITIES:
            errors.append(f"invalid review_priority={row.get('review_priority', '')}")
        if errors:
            invalid_rows.append(f"line {index} {row.get('segment_id', '')}: {'; '.join(errors)}")

    print(f"Total rows: {len(rows)}")
    print("Count by review_priority:")
    for priority, count in Counter(row.get("review_priority", "") for row in rows).most_common():
        print(f"- {priority or '(blank)'}: {count}")
    print("Count by adjudication_status:")
    for status, count in Counter(row.get("adjudication_status", "") for row in rows).most_common():
        print(f"- {status or '(blank)'}: {count}")
    blank_adjudicated = sum(1 for row in rows if not row.get("adjudicated_role", ""))
    print(f"Blank adjudicated_role: {blank_adjudicated}")
    print(f"Invalid rows: {len(invalid_rows)}")
    for item in invalid_rows:
        print(f"- {item}")
    print("Validation result: PASS" if not invalid_rows else "Validation result: FAIL")


if __name__ == "__main__":
    main()
