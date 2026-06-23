import csv
import shutil
from collections import Counter
from pathlib import Path


REVIEW_PATH = Path("data/v1/gold/role_adjudication_review_v2_fresh.csv")
BACKUP_PATH = Path("data/v1/gold/role_adjudication_review_v2_fresh.before_p2_adjudication.csv")
SUMMARY_PATH = Path("data/v1/gold/P2_ADJUDICATION_SUMMARY.md")

ADJUDICATIONS = {
    "HELDOUT2_S0021": ("DEFINE", "ACCEPT_GOLD", "Colon form gives the identity of route provenance.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0022": ("DEFINE", "ACCEPT_GOLD", "Names the visible sequence, so the sentence defines retrieval trace.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0023": ("DEFINE", "ACCEPT_GOLD", "Covers gives the boundary of consent boundary.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0025": ("DEFINE", "ACCEPT_GOLD", "Describes what agent memory routing means.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0018": ("CLAIM", "ACCEPT_GOLD", "Sentence asserts the value condition for human review.", "MULTIWAY_AMBIGUOUS"),
    "HELDOUT2_S0038": ("METHOD", "ACCEPT_GOLD", "Route uncertain answers describes a reusable review procedure.", "NEXT_STEP_METHOD_BOUNDARY"),
    "HELDOUT2_S0073": ("EXAMPLE", "ACCEPT_GOLD", "Support-chatbot case is a concrete permission-boundary scenario.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0074": ("EXAMPLE", "ACCEPT_GOLD", "Coding task is a concrete memory-selection scenario.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0077": ("EXAMPLE", "ACCEPT_GOLD", "Incident operator tracing logs is a concrete scenario.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0051": ("LIMITATION", "ACCEPT_GOLD", "May overstate generalisation states a caveat despite future wording.", "NONE"),
    "HELDOUT2_S0053": ("LIMITATION", "ACCEPT_GOLD", "Too stale to justify action is an insufficiency caveat.", "NONE"),
    "HELDOUT2_S0060": ("LIMITATION", "ACCEPT_GOLD", "Fragile if labels drift states a boundary/failure mode.", "NONE"),
    "HELDOUT2_S0063": ("NEXT_STEP", "ACCEPT_GOLD", "Add examples proposes future test data.", "NEXT_STEP_METHOD_BOUNDARY"),
    "HELDOUT2_S0068": ("NEXT_STEP", "ACCEPT_GOLD", "Build noisy benchmark rows proposes future benchmark construction.", "NEXT_STEP_METHOD_BOUNDARY"),
    "HELDOUT2_S0041": ("RESULT", "ACCEPT_GOLD", "Recovered more passages reports evaluation-run output.", "RESULT_CLAIM_BOUNDARY"),
    "HELDOUT2_S0046": ("RESULT", "ACCEPT_GOLD", "Exposed brittle behaviour reports benchmark outcome.", "RESULT_CLAIM_BOUNDARY"),
}

def load_rows():
    with REVIEW_PATH.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        return list(reader.fieldnames or []), list(reader)


def write_rows(fieldnames, rows):
    with REVIEW_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(p2_rows):
    status_counts = Counter(row["adjudication_status"] for row in p2_rows)
    role_counts = Counter(row["adjudicated_role"] for row in p2_rows)
    issue_counts = Counter(row["rubric_issue"] for row in p2_rows)
    changed = [row for row in p2_rows if row["adjudicated_role"] != row["gold_role"]]
    second_review = [
        row
        for row in p2_rows
        if row["adjudication_status"] in {"NEEDS_SECOND_REVIEW", "RUBRIC_AMBIGUOUS"}
    ]

    lines = [
        "# P2 Role Adjudication Summary",
        "",
        f"- Total P2 rows: {len(p2_rows)}",
        f"- ACCEPT_GOLD: {status_counts.get('ACCEPT_GOLD', 0)}",
        f"- CHANGE_GOLD: {status_counts.get('CHANGE_GOLD', 0)}",
        f"- NEEDS_SECOND_REVIEW: {status_counts.get('NEEDS_SECOND_REVIEW', 0)}",
        f"- RUBRIC_AMBIGUOUS: {status_counts.get('RUBRIC_AMBIGUOUS', 0)}",
        "",
        "## Count By Adjudicated Role",
        "",
        "| adjudicated_role | count |",
        "|---|---:|",
    ]
    for role, count in role_counts.most_common():
        lines.append(f"| {role} | {count} |")

    lines.extend(["", "## Count By Rubric Issue", "", "| rubric_issue | count |", "|---|---:|"])
    for issue, count in issue_counts.most_common():
        lines.append(f"| {issue} | {count} |")

    lines.extend([
        "",
        "## Rows Where Gold Role Changed",
        "",
        "| segment_id | gold_role | adjudicated_role | reason |",
        "|---|---|---|---|",
    ])
    if changed:
        for row in changed:
            lines.append(
                f"| {row['segment_id']} | {row['gold_role']} | {row['adjudicated_role']} | {row['adjudication_reason']} |"
            )
    else:
        lines.append("| none |  |  |  |")

    lines.extend([
        "",
        "## Rows Needing Second Review",
        "",
        "| segment_id | gold_role | adjudicated_role | status | reason |",
        "|---|---|---|---|---|",
    ])
    if second_review:
        for row in second_review:
            lines.append(
                f"| {row['segment_id']} | {row['gold_role']} | {row['adjudicated_role']} | "
                f"{row['adjudication_status']} | {row['adjudication_reason']} |"
            )
    else:
        lines.append("| none |  |  |  |  |")

    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    fieldnames, rows = load_rows()
    p2_blank_ids = {
        row["segment_id"]
        for row in rows
        if row.get("review_priority") == "P2" and not row.get("adjudicated_role")
    }
    missing = p2_blank_ids - set(ADJUDICATIONS)
    extra = set(ADJUDICATIONS) - p2_blank_ids
    if missing or extra:
        raise SystemExit(f"P2 adjudication mismatch: missing={sorted(missing)} extra={sorted(extra)}")

    shutil.copyfile(REVIEW_PATH, BACKUP_PATH)

    for row in rows:
        if row.get("review_priority") == "P2" and not row.get("adjudicated_role"):
            role, status, reason, issue = ADJUDICATIONS[row["segment_id"]]
            row["adjudicated_role"] = role
            row["adjudication_status"] = status
            row["adjudication_reason"] = reason
            row["rubric_issue"] = issue

    write_rows(fieldnames, rows)
    p2_rows = [row for row in rows if row.get("review_priority") == "P2"]
    write_summary(p2_rows)

    blank_adjudicated = sum(1 for row in rows if not row.get("adjudicated_role"))
    all_filled = [row for row in rows if row.get("adjudicated_role")]
    all_status_counts = Counter(row["adjudication_status"] for row in all_filled)
    p2_status_counts = Counter(row["adjudication_status"] for row in p2_rows)
    changed_count = sum(1 for row in p2_rows if row["adjudicated_role"] != row["gold_role"])

    print(f"Backup path: {BACKUP_PATH}")
    print(f"Review CSV path: {REVIEW_PATH}")
    print(f"Total P2 rows filled: {len(p2_rows)}")
    print(f"Remaining blank adjudicated_role count: {blank_adjudicated}")
    print("Status counts across all filled rows:")
    for status in ["ACCEPT_GOLD", "CHANGE_GOLD", "NEEDS_SECOND_REVIEW", "RUBRIC_AMBIGUOUS"]:
        print(f"- {status}: {all_status_counts.get(status, 0)}")
    print("P2-only status counts:")
    for status in ["ACCEPT_GOLD", "CHANGE_GOLD", "NEEDS_SECOND_REVIEW", "RUBRIC_AMBIGUOUS"]:
        print(f"- {status}: {p2_status_counts.get(status, 0)}")
    print(f"Changed gold-role candidate count: {changed_count}")
    print(f"Summary path: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
