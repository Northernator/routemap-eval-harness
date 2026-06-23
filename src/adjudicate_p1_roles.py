import csv
import shutil
from collections import Counter
from pathlib import Path


REVIEW_PATH = Path("data/v1/gold/role_adjudication_review_v2_fresh.csv")
BACKUP_PATH = Path("data/v1/gold/role_adjudication_review_v2_fresh.before_p1_adjudication.csv")
SUMMARY_PATH = Path("data/v1/gold/P1_ADJUDICATION_SUMMARY.md")

ADJUDICATIONS = {
    "HELDOUT2_S0001": ("BACKGROUND", "ACCEPT_GOLD", "Policy overview frames source context rather than a reusable thesis.", "BACKGROUND_CLAIM_BOUNDARY"),
    "HELDOUT2_S0002": ("BACKGROUND", "ACCEPT_GOLD", "Release archive describes document contents and rationale.", "NONE"),
    "HELDOUT2_S0003": ("BACKGROUND", "ACCEPT_GOLD", "Privacy handbook gives context before annotation work.", "NONE"),
    "HELDOUT2_S0006": ("BACKGROUND", "ACCEPT_GOLD", "Tool-use security note records vocabulary context.", "NONE"),
    "HELDOUT2_S0008": ("BACKGROUND", "ACCEPT_GOLD", "Evidence selection primer describes policy context for reviewers.", "BACKGROUND_CLAIM_BOUNDARY"),
    "HELDOUT2_S0009": ("BACKGROUND", "ACCEPT_GOLD", "Governance catalog summarizes terminology and approval roles.", "NONE"),
    "HELDOUT2_S0017": ("CLAIM", "ACCEPT_GOLD", "Sentence asserts a reusable thesis about benchmark design weakness.", "BACKGROUND_CLAIM_BOUNDARY"),
    "HELDOUT2_S0020": ("CLAIM", "ACCEPT_GOLD", "Sentence argues what an audit trail demonstrates without answer support.", "LIMITATION_CLAIM_BOUNDARY"),
    "HELDOUT2_S0024": ("DEFINE", "ACCEPT_GOLD", "Denotes gives the identity of model release governance.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0028": ("DEFINE", "ACCEPT_GOLD", "Names records that reconstruct a decision, so this defines audit trail.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0029": ("DEFINE", "ACCEPT_GOLD", "Labels identifies what a control surface means.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0030": ("DEFINE", "ACCEPT_GOLD", "Names a decision point and gives term identity.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0080": ("EXAMPLE", "ACCEPT_GOLD", "Final-answer case is a concrete support-failure scenario.", "MULTIWAY_AMBIGUOUS"),
    "HELDOUT2_S0039": ("METHOD", "ACCEPT_GOLD", "Imperative store describes a reusable audit procedure.", "NONE"),
    "HELDOUT2_S0013": ("CLAIM", "ACCEPT_GOLD", "Sentence asserts a thesis about consent boundaries losing force.", "MULTIWAY_AMBIGUOUS"),
    "HELDOUT2_S0057": ("LIMITATION", "ACCEPT_GOLD", "Constrained signals a caveat about human review evidence.", "NONE"),
    "HELDOUT2_S0034": ("METHOD", "ACCEPT_GOLD", "Rank memory candidates describes a reusable procedure.", "NONE"),
    "HELDOUT2_S0067": ("NEXT_STEP", "NEEDS_SECOND_REVIEW", "Could read as current instruction, but row proposes a future evaluation question.", "NEXT_STEP_METHOD_BOUNDARY"),
    "HELDOUT2_S0056": ("LIMITATION", "ACCEPT_GOLD", "Not enough states insufficiency of permission checks.", "NONE"),
    "HELDOUT2_S0065": ("NEXT_STEP", "ACCEPT_GOLD", "Run a benchmark proposes a future evaluation action.", "NEXT_STEP_METHOD_BOUNDARY"),
    "HELDOUT2_S0072": ("EXAMPLE", "ACCEPT_GOLD", "Suppose introduces a concrete release-board scenario.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0076": ("EXAMPLE", "ACCEPT_GOLD", "Plugin case illustrates a concrete tool-use security scenario.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0032": ("METHOD", "ACCEPT_GOLD", "Before launch collect describes an approval procedure.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0035": ("METHOD", "ACCEPT_GOLD", "Log tool calls describes a reusable security procedure.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0036": ("METHOD", "ACCEPT_GOLD", "Connect symptoms to traces and controls describes incident-review procedure.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0070": ("NEXT_STEP", "ACCEPT_GOLD", "Create cases proposes future answer-support test data.", "NEXT_STEP_METHOD_BOUNDARY"),
    "HELDOUT2_S0042": ("RESULT", "ACCEPT_GOLD", "Resolved faster reports an observed review outcome.", "RESULT_CLAIM_BOUNDARY"),
    "HELDOUT2_S0044": ("RESULT", "ACCEPT_GOLD", "Returned older but relevant context reports observed memory-routing behaviour.", "RESULT_CLAIM_BOUNDARY"),
    "HELDOUT2_S0047": ("RESULT", "ACCEPT_GOLD", "Human reviewers agreed more often reports an observed review outcome.", "RESULT_CLAIM_BOUNDARY"),
    "HELDOUT2_S0049": ("RESULT", "ACCEPT_GOLD", "Improved after grouping reports an observed evidence-selection outcome.", "RESULT_CLAIM_BOUNDARY"),
    "HELDOUT2_S0043": ("RESULT", "ACCEPT_GOLD", "Produced fewer false positives reports an observed test outcome.", "RESULT_CLAIM_BOUNDARY"),
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


def write_summary(p1_rows):
    status_counts = Counter(row["adjudication_status"] for row in p1_rows)
    role_counts = Counter(row["adjudicated_role"] for row in p1_rows)
    issue_counts = Counter(row["rubric_issue"] for row in p1_rows)
    changed = [row for row in p1_rows if row["adjudicated_role"] != row["gold_role"]]
    second_review = [
        row
        for row in p1_rows
        if row["adjudication_status"] in {"NEEDS_SECOND_REVIEW", "RUBRIC_AMBIGUOUS"}
    ]

    lines = [
        "# P1 Role Adjudication Summary",
        "",
        f"- Total P1 rows: {len(p1_rows)}",
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
    p1_ids = {row["segment_id"] for row in rows if row.get("review_priority") == "P1"}
    missing = p1_ids - set(ADJUDICATIONS)
    extra = set(ADJUDICATIONS) - p1_ids
    if missing or extra:
        raise SystemExit(f"P1 adjudication mismatch: missing={sorted(missing)} extra={sorted(extra)}")

    shutil.copyfile(REVIEW_PATH, BACKUP_PATH)

    for row in rows:
        if row.get("review_priority") == "P1":
            role, status, reason, issue = ADJUDICATIONS[row["segment_id"]]
            row["adjudicated_role"] = role
            row["adjudication_status"] = status
            row["adjudication_reason"] = reason
            row["rubric_issue"] = issue
        elif row.get("review_priority") in {"P2", "P3", "P4"}:
            row["adjudicated_role"] = ""
            row["adjudication_status"] = ""
            row["adjudication_reason"] = ""
            row["rubric_issue"] = ""

    write_rows(fieldnames, rows)
    p1_rows = [row for row in rows if row.get("review_priority") == "P1"]
    write_summary(p1_rows)

    blank_adjudicated = sum(1 for row in rows if not row.get("adjudicated_role"))
    status_counts = Counter(row["adjudication_status"] for row in p1_rows)
    changed_count = sum(1 for row in p1_rows if row["adjudicated_role"] != row["gold_role"])

    print(f"Backup path: {BACKUP_PATH}")
    print(f"Review CSV path: {REVIEW_PATH}")
    print(f"Total P1 rows filled: {len(p1_rows)}")
    print(f"Remaining blank adjudicated_role count: {blank_adjudicated}")
    print("Status counts:")
    for status in ["ACCEPT_GOLD", "CHANGE_GOLD", "NEEDS_SECOND_REVIEW", "RUBRIC_AMBIGUOUS"]:
        print(f"- {status}: {status_counts.get(status, 0)}")
    print(f"Changed gold-role candidate count: {changed_count}")
    print(f"Summary path: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
