import csv
import shutil
from collections import Counter
from pathlib import Path


REVIEW_PATH = Path("data/v1/gold/role_adjudication_review_v2_fresh.csv")
BACKUP_PATH = Path("data/v1/gold/role_adjudication_review_v2_fresh.before_p3_adjudication.csv")
SUMMARY_PATH = Path("data/v1/gold/P3_ADJUDICATION_SUMMARY.md")

ADJUDICATIONS = {
    "HELDOUT2_S0005": ("BACKGROUND", "ACCEPT_GOLD", "Briefing sets document scope and context despite risk terms.", "BACKGROUND_CLAIM_BOUNDARY"),
    "HELDOUT2_S0007": ("BACKGROUND", "ACCEPT_GOLD", "Appendix lists benchmark package contents and review artifacts.", "BACKGROUND_CLAIM_BOUNDARY"),
    "HELDOUT2_S0010": ("BACKGROUND", "ACCEPT_GOLD", "Playbook provides contextual background and explicitly avoids recommending a classifier.", "BACKGROUND_CLAIM_BOUNDARY"),
    "HELDOUT2_S0014": ("CLAIM", "ACCEPT_GOLD", "Sentence argues why retrieval traces matter for answer support.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0015": ("CLAIM", "ACCEPT_GOLD", "Sentence asserts a behaviour risk of agent memory without provenance.", "CLAIM_DEFINE_BOUNDARY"),
    "HELDOUT2_S0016": ("CLAIM", "ACCEPT_GOLD", "Sentence asserts a thesis about controls failing to affect review behaviour.", "MULTIWAY_AMBIGUOUS"),
    "HELDOUT2_S0031": ("METHOD", "ACCEPT_GOLD", "Compare and flag are procedural actions for review.", "NONE"),
    "HELDOUT2_S0040": ("METHOD", "ACCEPT_GOLD", "Label, record, and adjudicate describe reusable annotation procedure.", "NONE"),
    "HELDOUT2_S0004": ("BACKGROUND", "ACCEPT_GOLD", "Documentation page introduces diagrams for unfamiliar teams.", "NONE"),
    "HELDOUT2_S0071": ("EXAMPLE", "ACCEPT_GOLD", "Hospital triage review is a concrete scenario.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0075": ("EXAMPLE", "ACCEPT_GOLD", "For instance introduces a concrete cited-paragraph scenario.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0078": ("EXAMPLE", "ACCEPT_GOLD", "Synthetic benchmark row is an illustrative concrete case.", "METHOD_EXAMPLE_BOUNDARY"),
    "HELDOUT2_S0054": ("LIMITATION", "ACCEPT_GOLD", "May miss reasoning steps states a caveat about retrieval traces.", "NONE"),
    "HELDOUT2_S0055": ("LIMITATION", "ACCEPT_GOLD", "Can preserve obsolete context unless reviewed states a failure mode.", "NONE"),
    "HELDOUT2_S0033": ("METHOD", "ACCEPT_GOLD", "Map consent records before selecting evidence is a procedure.", "NONE"),
    "HELDOUT2_S0061": ("NEXT_STEP", "ACCEPT_GOLD", "Next assemble a split proposes future dataset work.", "NEXT_STEP_METHOD_BOUNDARY"),
    "HELDOUT2_S0062": ("NEXT_STEP", "ACCEPT_GOLD", "Future evaluation proposes a comparison test.", "NEXT_STEP_METHOD_BOUNDARY"),
    "HELDOUT2_S0066": ("NEXT_STEP", "ACCEPT_GOLD", "Follow-up set should include cases proposes future benchmark content.", "NEXT_STEP_METHOD_BOUNDARY"),
    "HELDOUT2_S0048": ("RESULT", "ACCEPT_GOLD", "Inspection showed presence reports an observed audit outcome.", "RESULT_CLAIM_BOUNDARY"),
    "HELDOUT2_S0050": ("RESULT", "ACCEPT_GOLD", "Mismatch review revealed confusion reports review outcome.", "RESULT_CLAIM_BOUNDARY"),
    "HELDOUT2_S0037": ("METHOD", "ACCEPT_GOLD", "Sample benchmark rows describes dataset construction procedure.", "NONE"),
    "HELDOUT2_S0045": ("RESULT", "ACCEPT_GOLD", "Review found an explanation for rejected actions.", "RESULT_CLAIM_BOUNDARY"),
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


def write_summary(p3_rows):
    status_counts = Counter(row["adjudication_status"] for row in p3_rows)
    role_counts = Counter(row["adjudicated_role"] for row in p3_rows)
    issue_counts = Counter(row["rubric_issue"] for row in p3_rows)
    changed = [row for row in p3_rows if row["adjudicated_role"] != row["gold_role"]]
    second_review = [
        row
        for row in p3_rows
        if row["adjudication_status"] in {"NEEDS_SECOND_REVIEW", "RUBRIC_AMBIGUOUS"}
    ]

    lines = [
        "# P3 Role Adjudication Summary",
        "",
        f"- Total P3 rows: {len(p3_rows)}",
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
    p3_blank_ids = {
        row["segment_id"]
        for row in rows
        if row.get("review_priority") == "P3" and not row.get("adjudicated_role")
    }
    missing = p3_blank_ids - set(ADJUDICATIONS)
    extra = set(ADJUDICATIONS) - p3_blank_ids
    if missing or extra:
        raise SystemExit(f"P3 adjudication mismatch: missing={sorted(missing)} extra={sorted(extra)}")

    shutil.copyfile(REVIEW_PATH, BACKUP_PATH)

    for row in rows:
        if row.get("review_priority") == "P3" and not row.get("adjudicated_role"):
            role, status, reason, issue = ADJUDICATIONS[row["segment_id"]]
            row["adjudicated_role"] = role
            row["adjudication_status"] = status
            row["adjudication_reason"] = reason
            row["rubric_issue"] = issue

    write_rows(fieldnames, rows)
    p3_rows = [row for row in rows if row.get("review_priority") == "P3"]
    write_summary(p3_rows)

    blank_adjudicated = sum(1 for row in rows if not row.get("adjudicated_role"))
    all_filled = [row for row in rows if row.get("adjudicated_role")]
    all_status_counts = Counter(row["adjudication_status"] for row in all_filled)
    p3_status_counts = Counter(row["adjudication_status"] for row in p3_rows)
    changed_count = sum(1 for row in p3_rows if row["adjudicated_role"] != row["gold_role"])

    print(f"Backup path: {BACKUP_PATH}")
    print(f"Review CSV path: {REVIEW_PATH}")
    print(f"Total P3 rows filled: {len(p3_rows)}")
    print(f"Remaining blank adjudicated_role count: {blank_adjudicated}")
    print("Status counts across all filled rows:")
    for status in ["ACCEPT_GOLD", "CHANGE_GOLD", "NEEDS_SECOND_REVIEW", "RUBRIC_AMBIGUOUS"]:
        print(f"- {status}: {all_status_counts.get(status, 0)}")
    print("P3-only status counts:")
    for status in ["ACCEPT_GOLD", "CHANGE_GOLD", "NEEDS_SECOND_REVIEW", "RUBRIC_AMBIGUOUS"]:
        print(f"- {status}: {p3_status_counts.get(status, 0)}")
    print(f"Changed gold-role candidate count: {changed_count}")
    print(f"Summary path: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
