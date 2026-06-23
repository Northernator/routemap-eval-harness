import csv
from pathlib import Path


INPUT_PATH = Path("data/v1/gold/role_adjudication_pack_v2_fresh.csv")
OUTPUT_PATH = Path("data/v1/gold/role_adjudication_review_v2_fresh.csv")
GUIDE_PATH = Path("data/v1/gold/ROLE_ADJUDICATION_REVIEW_GUIDE_V2_FRESH.md")

ADDED_COLUMNS = [
    "adjudicated_role",
    "adjudication_status",
    "adjudication_reason",
    "rubric_issue",
    "review_priority",
]

PRIORITY_BY_PATTERN = {
    "all_wrong_same": "P1",
    "all_wrong_different": "P1",
    "nb_only_correct": "P2",
    "rule_only_correct": "P2",
    "hybrid_only_correct": "P2",
    "rule_and_nb_correct": "P3",
    "rule_and_hybrid_correct": "P3",
    "nb_and_hybrid_correct": "P3",
    "all_correct": "P4",
}

PRIORITY_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}


def review_priority(row):
    return PRIORITY_BY_PATTERN.get(row.get("agreement_pattern", ""), "P4")


def sort_key(row):
    priority = review_priority(row)
    return (
        PRIORITY_ORDER.get(priority, 9),
        row.get("likely_ambiguity_type", ""),
        row.get("gold_role", ""),
        row.get("segment_id", ""),
    )


def write_guide():
    lines = [
        "# Role Adjudication Review Guide v2 Fresh",
        "",
        "## Purpose",
        "",
        "This review file supports manual adjudication of ambiguous role labels in the fresh held-out v2 dataset. The goal is to decide whether current `gold_role` labels should be accepted, changed later, or sent for additional review. This step does not create a corrected gold file.",
        "",
        "## Model Predictions",
        "",
        "Do not trust model predictions blindly. Rule, Naive Bayes, and hybrid predictions are included to reveal disagreement patterns and likely ambiguity boundaries. Treat them as review signals, not votes that automatically override `gold_role`.",
        "",
        "## How To Fill The Review CSV",
        "",
        "- `adjudicated_role`: leave blank until reviewed, then enter one role: BACKGROUND, CLAIM, DEFINE, METHOD, RESULT, LIMITATION, NEXT_STEP, or EXAMPLE.",
        "- `adjudication_status`: leave blank until reviewed, then use ACCEPT_GOLD, CHANGE_GOLD, NEEDS_SECOND_REVIEW, or RUBRIC_AMBIGUOUS.",
        "- `adjudication_reason`: write a short explanation for the decision, especially when changing or questioning the gold role.",
        "- `rubric_issue`: leave blank until reviewed, then use NONE or one boundary value: CLAIM_DEFINE_BOUNDARY, METHOD_EXAMPLE_BOUNDARY, RESULT_CLAIM_BOUNDARY, BACKGROUND_CLAIM_BOUNDARY, LIMITATION_CLAIM_BOUNDARY, NEXT_STEP_METHOD_BOUNDARY, or MULTIWAY_AMBIGUOUS.",
        "- `review_priority`: prefilled from model agreement. Do not edit unless regenerating the file from the pack.",
        "",
        "## Tie-Break Rules",
        "",
        "### BACKGROUND vs CLAIM",
        "",
        "- BACKGROUND if the sentence mainly describes a source, document, project, page, or context.",
        "- CLAIM if the sentence asserts a reusable thesis that could directly support an answer.",
        "",
        "### CLAIM vs DEFINE",
        "",
        "- DEFINE if the sentence gives the meaning, boundary, or identity of a term.",
        "- CLAIM if it argues a point about how something behaves or why it matters.",
        "",
        "### METHOD vs EXAMPLE",
        "",
        "- METHOD if it tells what to do or describes a reusable procedure.",
        "- EXAMPLE if it gives a concrete scenario or instance.",
        "",
        "### RESULT vs CLAIM",
        "",
        "- RESULT if it reports what a run, evaluation, test, document, or benchmark produced/shows.",
        "- CLAIM if it is a general assertion not tied to a produced/evaluated outcome.",
        "",
        "### LIMITATION vs CLAIM",
        "",
        "- LIMITATION if the main function is caveat, insufficiency, boundary, failure mode, or constraint.",
        "- CLAIM if the sentence is broader thesis language with negative wording but not mainly a caveat.",
        "",
        "### NEXT_STEP vs METHOD",
        "",
        "- NEXT_STEP if it proposes future work, a future benchmark, or a follow-up test.",
        "- METHOD if it describes an existing procedure or how to perform a task now.",
        "",
        "## Review Order",
        "",
        "1. First review P1 rows.",
        "2. Then review rows with `claim_vs_define`, `background_vs_claim`, and `claim_vs_method`.",
        "3. Leave `all_correct` rows until last.",
        "",
        "## Status Guidance",
        "",
        "- Use ACCEPT_GOLD when `gold_role` is correct under the rubric.",
        "- Use CHANGE_GOLD when the reviewer believes `gold_role` should change later.",
        "- Use NEEDS_SECOND_REVIEW when the row needs another reviewer before a decision.",
        "- Use RUBRIC_AMBIGUOUS when the rubric itself does not resolve the row cleanly.",
    ]
    GUIDE_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    with INPUT_PATH.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        original_fields = list(reader.fieldnames or [])
        rows = list(reader)

    output_rows = []
    for row in rows:
        row = dict(row)
        row["adjudicated_role"] = ""
        row["adjudication_status"] = ""
        row["adjudication_reason"] = ""
        row["rubric_issue"] = ""
        row["review_priority"] = review_priority(row)
        output_rows.append(row)

    output_rows.sort(key=sort_key)
    output_fields = original_fields + [column for column in ADDED_COLUMNS if column not in original_fields]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(output_rows)

    write_guide()
    print(f"Rows written: {len(output_rows)}")
    print(f"Review CSV: {OUTPUT_PATH}")
    print(f"Review guide: {GUIDE_PATH}")


if __name__ == "__main__":
    main()
