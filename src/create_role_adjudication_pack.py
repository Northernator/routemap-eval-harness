import argparse
import csv
from collections import Counter
from pathlib import Path


GOLD_PATH = Path("data/v1/gold/heldout_full_extraction_gold_v2.csv")
RULE_PATH = Path("data/v1/gold/heldout_full_extraction_pred_v2_fresh.csv")
NB_PATH = Path("data/v1/gold/heldout_role_nb_pred_v2_fresh.csv")
HYBRID_PATH = Path("data/v1/gold/heldout_role_hybrid_nb_rules_pred_v2_fresh.csv")
RUBRIC_PATH = Path("data/v1/gold/ROLE_LABEL_RUBRIC_V2.md")

COMMONLY_CONFUSED_ROLES = {"CLAIM", "DEFINE", "METHOD", "RESULT", "BACKGROUND", "EXAMPLE"}

PACK_FIELDS = [
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
]

AMBIGUITY_QUESTIONS = {
    "claim_vs_define": "Is this sentence defining a term, or asserting a thesis about it?",
    "method_vs_example": "Is this a procedure to perform, or a concrete example of a procedure?",
    "result_vs_claim": "Is this reporting an evaluation outcome, or making a general claim?",
    "result_vs_method": "Is this reporting what happened, or describing what to do?",
    "background_vs_claim": "Is this source context, or a substantive claim?",
    "background_vs_limitation": "Is this a caveat/constraint, or merely background context?",
    "claim_vs_method": "Is this recommending an action, or asserting a broader thesis?",
    "multiway_ambiguous": "Which single role best captures the sentence's main job in the route?",
    "low_ambiguity": "Do the label and predictions reflect the sentence's main route role?",
}


def read_by_segment(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return {row["segment_id"]: row for row in csv.DictReader(source)}


def agreement_pattern(gold, pred_rule, pred_nb, pred_hybrid):
    correct = {
        "rule": pred_rule == gold,
        "nb": pred_nb == gold,
        "hybrid": pred_hybrid == gold,
    }
    count = sum(correct.values())
    if count == 3:
        return "all_correct"
    if count == 0:
        return "all_wrong_same" if len({pred_rule, pred_nb, pred_hybrid}) == 1 else "all_wrong_different"
    if count == 1:
        if correct["rule"]:
            return "rule_only_correct"
        if correct["nb"]:
            return "nb_only_correct"
        return "hybrid_only_correct"
    if correct["rule"] and correct["nb"]:
        return "rule_and_nb_correct"
    if correct["rule"] and correct["hybrid"]:
        return "rule_and_hybrid_correct"
    return "nb_and_hybrid_correct"


def infer_ambiguity_type(gold, predictions):
    labels = {gold, *predictions}
    if len(labels) > 3:
        return "multiway_ambiguous"
    pairs = [
        ("claim_vs_define", {"CLAIM", "DEFINE"}),
        ("method_vs_example", {"METHOD", "EXAMPLE"}),
        ("result_vs_claim", {"RESULT", "CLAIM"}),
        ("result_vs_method", {"RESULT", "METHOD"}),
        ("background_vs_claim", {"BACKGROUND", "CLAIM"}),
        ("background_vs_limitation", {"BACKGROUND", "LIMITATION"}),
        ("claim_vs_method", {"CLAIM", "METHOD"}),
    ]
    for name, pair in pairs:
        if pair <= labels:
            return name
    if len(labels) > 2:
        return "multiway_ambiguous"
    return "low_ambiguity"


def make_pack_rows():
    gold_rows = read_by_segment(GOLD_PATH)
    rule_rows = read_by_segment(RULE_PATH)
    nb_rows = read_by_segment(NB_PATH)
    hybrid_rows = read_by_segment(HYBRID_PATH)
    pack_rows = []

    for segment_id in sorted(gold_rows):
        gold_row = gold_rows[segment_id]
        gold = gold_row.get("gold_role", "")
        pred_rule = rule_rows[segment_id].get("pred_role", "")
        pred_nb = nb_rows[segment_id].get("pred_role_nb", "")
        pred_hybrid = hybrid_rows[segment_id].get("pred_role_hybrid", "")
        predictions = [pred_rule, pred_nb, pred_hybrid]
        pattern = agreement_pattern(gold, pred_rule, pred_nb, pred_hybrid)
        ambiguity = infer_ambiguity_type(gold, predictions)
        needs_review = (
            pattern != "all_correct"
            or len(set(predictions)) > 1
            or gold in COMMONLY_CONFUSED_ROLES
        )
        pack_rows.append({
            "segment_id": segment_id,
            "title": gold_row.get("title", ""),
            "text": gold_row.get("text", ""),
            "gold_role": gold,
            "pred_rule": pred_rule,
            "pred_nb": pred_nb,
            "pred_hybrid": pred_hybrid,
            "agreement_pattern": pattern,
            "needs_review": "YES" if needs_review else "NO",
            "likely_ambiguity_type": ambiguity,
            "suggested_review_question": AMBIGUITY_QUESTIONS[ambiguity],
            "notes": gold_row.get("notes", ""),
        })
    return pack_rows


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=PACK_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows):
    lines = ["| segment_id | gold | rule | nb | hybrid | pattern | ambiguity | question | text |", "|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        text = " ".join(row["text"].split())[:140]
        lines.append(
            f"| {row['segment_id']} | {row['gold_role']} | {row['pred_rule']} | {row['pred_nb']} | "
            f"{row['pred_hybrid']} | {row['agreement_pattern']} | {row['likely_ambiguity_type']} | "
            f"{row['suggested_review_question']} | {text} |"
        )
    return lines


def review_priority(row):
    pattern_rank = {
        "all_wrong_same": 0,
        "all_wrong_different": 1,
        "nb_only_correct": 2,
        "rule_only_correct": 3,
        "hybrid_only_correct": 4,
        "rule_and_nb_correct": 5,
        "rule_and_hybrid_correct": 6,
        "nb_and_hybrid_correct": 7,
        "all_correct": 8,
    }
    predictions_disagree = len({row["pred_rule"], row["pred_nb"], row["pred_hybrid"]}) > 1
    common_role = row["gold_role"] in COMMONLY_CONFUSED_ROLES
    return (
        pattern_rank.get(row["agreement_pattern"], 9),
        0 if predictions_disagree else 1,
        0 if common_role else 1,
        row["segment_id"],
    )


def write_markdown(path, rows):
    path = Path(path)
    pattern_counts = Counter(row["agreement_pattern"] for row in rows)
    ambiguity_counts = Counter(row["likely_ambiguity_type"] for row in rows)
    needs_review = [row for row in rows if row["needs_review"] == "YES"]
    priority_rows = sorted(needs_review, key=review_priority)

    lines = [
        "# Role Adjudication Pack: Fresh Held-Out v2",
        "",
        "## Summary",
        "",
        f"- Total rows: {len(rows)}",
        f"- Rows needing review: {len(needs_review)}",
        "- Purpose: support human adjudication of ambiguous role labels without changing gold labels automatically.",
        "",
        "## Agreement Patterns",
        "",
        "| agreement_pattern | count |",
        "|---|---:|",
    ]
    for pattern, count in pattern_counts.most_common():
        lines.append(f"| {pattern} | {count} |")

    lines.extend(["", "## Likely Ambiguity Types", "", "| likely_ambiguity_type | count |", "|---|---:|"])
    for ambiguity, count in ambiguity_counts.most_common():
        lines.append(f"| {ambiguity} | {count} |")

    lines.extend(["", "## Top 15 Rows To Review First", ""])
    lines.extend(markdown_table(priority_rows[:15]))

    lines.extend(["", "## All Rows Needing Review", ""])
    lines.extend(markdown_table(needs_review))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_rubric():
    lines = [
        "# Role Label Rubric v2",
        "",
        "Use this rubric when adjudicating fresh held-out v2 role labels. Assign the role that best describes the sentence's main job in a route, not every possible secondary function.",
        "",
        "## Role Definitions",
        "",
        "- BACKGROUND: source, document, project, policy, or dataset context. It frames where information comes from or why it exists.",
        "- CLAIM: a substantive thesis, principle, or assertion about a system, risk, method, evidence, or governance practice.",
        "- DEFINE: a term/category explanation. It names what something means, covers, denotes, or is called.",
        "- METHOD: an action, procedure, workflow, or implementation step to perform.",
        "- RESULT: an observed or reported outcome from evaluation, review, benchmark, test, inspection, or document output.",
        "- LIMITATION: a caveat, insufficiency, constraint, boundary, failure mode, or warning.",
        "- NEXT_STEP: proposed future work, future evaluation, future dataset construction, or follow-up testing.",
        "- EXAMPLE: a concrete instance, scenario, case, or illustrative situation.",
        "",
        "## Common Confusions",
        "",
        "### CLAIM vs DEFINE",
        "",
        "- DEFINE names what a term/category means.",
        "- CLAIM argues something about a system, risk, method, or principle.",
        "",
        "Examples:",
        "",
        "- HELDOUT2_S0021 DEFINE: `Route provenance: the documented lineage connecting source context, selected evidence, and answer support.`",
        "- HELDOUT2_S0014 CLAIM: `A retrieval trace matters because answer support depends on the path, not merely on a cited passage.`",
        "- HELDOUT2_S0029 DEFINE: `Control surface labels the places where safeguards can change model, tool, or data behaviour.`",
        "",
        "### METHOD vs EXAMPLE",
        "",
        "- METHOD says what to do or how to do it.",
        "- EXAMPLE gives a concrete instance/scenario.",
        "",
        "Examples:",
        "",
        "- HELDOUT2_S0031 METHOD: `Compare each generated answer against its retrieval trace, then flag unsupported assertions for review.`",
        "- HELDOUT2_S0076 EXAMPLE: `A plugin that reads calendars and sends email illustrates why tool-use security needs separate route checks.`",
        "- HELDOUT2_S0078 EXAMPLE: `A synthetic benchmark row could look procedural while actually describing a concrete reviewer scenario.`",
        "",
        "### RESULT vs CLAIM",
        "",
        "- RESULT reports an observed/evaluated outcome or expected output of a document/test.",
        "- CLAIM states a thesis or principle.",
        "",
        "Examples:",
        "",
        "- HELDOUT2_S0041 RESULT: `The evaluation run recovered more answer-support passages after route provenance was kept with the snippets.`",
        "- HELDOUT2_S0011 CLAIM: `AI safety evaluation becomes more credible when disagreement remains traceable instead of hidden behind an average.`",
        "- HELDOUT2_S0050 RESULT: `The mismatch review revealed that policy-context rows were often confused with broad claims.`",
        "",
        "### BACKGROUND vs CLAIM",
        "",
        "- BACKGROUND gives source/project context.",
        "- CLAIM gives a substantive assertion that can support an answer.",
        "",
        "Examples:",
        "",
        "- HELDOUT2_S0001 BACKGROUND: `A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric exercise.`",
        "- HELDOUT2_S0007 BACKGROUND: `A benchmark design appendix lists source context, gold labels, and mismatch review artifacts for auditors.`",
        "- HELDOUT2_S0017 CLAIM: `Benchmark design is weaker when easy source context outnumbers adversarial route segments.`",
        "",
        "### LIMITATION vs CLAIM",
        "",
        "- LIMITATION states a caveat, insufficiency, boundary, or failure mode.",
        "- CLAIM is broader and not mainly about insufficiency.",
        "",
        "Examples:",
        "",
        "- HELDOUT2_S0052 LIMITATION: `A complete release packet does not prove that the deployed model will behave safely after integration.`",
        "- HELDOUT2_S0058 LIMITATION: `A route benchmark remains incomplete without operational incidents, adversarial examples, and noisy documentation.`",
        "- HELDOUT2_S0012 CLAIM: `Model release governance should treat missing evidence as a decision risk, not as harmless paperwork.`",
        "",
        "### NEXT_STEP vs METHOD",
        "",
        "- NEXT_STEP proposes future work/evaluation.",
        "- METHOD describes an action or procedure inside the current system.",
        "",
        "Examples:",
        "",
        "- HELDOUT2_S0064 NEXT_STEP: `The next retrieval test should hide titles and require the extractor to infer route provenance from text alone.`",
        "- HELDOUT2_S0067 NEXT_STEP: `Evaluate whether human review changes final answers when rejected evidence is shown.`",
        "- HELDOUT2_S0038 METHOD: `Route uncertain answers to human review when evidence selection conflicts with the final answer.`",
        "",
        "## Adjudication Notes",
        "",
        "- Prefer the sentence's main communicative function over isolated trigger words.",
        "- If a sentence contains both a scenario and a recommendation, choose EXAMPLE only when the concrete scenario is the main point.",
        "- If a sentence contains future-looking words but mainly warns about insufficiency, choose LIMITATION.",
        "- Do not change labels automatically from model disagreement alone; use disagreement to prioritize human review.",
    ]
    RUBRIC_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    rows = make_pack_rows()
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows)
    write_rubric()

    print(f"Total rows: {len(rows)}")
    print(f"Rows needing review: {sum(1 for row in rows if row['needs_review'] == 'YES')}")
    print(f"Wrote CSV: {args.out_csv}")
    print(f"Wrote markdown: {args.out_md}")
    print(f"Wrote rubric: {RUBRIC_PATH}")


if __name__ == "__main__":
    main()
