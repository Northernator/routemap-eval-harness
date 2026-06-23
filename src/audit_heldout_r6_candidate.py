import csv
import json
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import split_entity_set
from role_taxonomies import map_role


ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = ROOT / "data/v1/heldout/r6_generalisation/predictions"
AUDIT_DIR = ROOT / "data/v1/heldout/r6_generalisation/audits"
OUT_CSV = AUDIT_DIR / "HELDOUT_R6_ROW_AUDIT.csv"
OUT_MD = AUDIT_DIR / "HELDOUT_R6_AUDIT.md"
OUT_JSON = AUDIT_DIR / "HELDOUT_R6_AUDIT_SUMMARY.json"

VARIANTS = {
    "combined": PRED_DIR / "combined_v3_heldout_predictions.csv",
    "D": PRED_DIR / "D_heldout_predictions.csv",
    "R6": PRED_DIR / "R6_heldout_predictions.csv",
}

REQUIRED = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "pred_role",
    "pred_entities",
    "pred_operative_status",
    "pred_relation",
    "pred_answer_relevant",
    "pred_valid",
]

AUDIT_FIELDS = [
    "segment_id",
    "gold_role",
    "combined_role",
    "D_role",
    "R6_role",
    "combined_role_correct",
    "D_role_correct",
    "R6_role_correct",
    "combined_coarse3_correct",
    "D_coarse3_correct",
    "R6_coarse3_correct",
    "gold_entities",
    "combined_entities",
    "D_entities",
    "R6_entities",
    "combined_entity_jaccard",
    "D_entity_jaccard",
    "R6_entity_jaccard",
    "combined_entity_exact",
    "D_entity_exact",
    "R6_entity_exact",
    "gold_status",
    "combined_status",
    "D_status",
    "R6_status",
    "combined_status_correct",
    "D_status_correct",
    "R6_status_correct",
    "gold_relation",
    "combined_relation",
    "D_relation",
    "R6_relation",
    "combined_relation_correct",
    "D_relation_correct",
    "R6_relation_correct",
    "gold_answer",
    "combined_answer",
    "D_answer",
    "R6_answer",
    "combined_answer_correct",
    "D_answer_correct",
    "R6_answer_correct",
    "combined_strict_correct",
    "D_strict_correct",
    "R6_strict_correct",
    "combined_relaxed_1_correct",
    "D_relaxed_1_correct",
    "R6_relaxed_1_correct",
    "combined_relaxed_2_correct",
    "D_relaxed_2_correct",
    "R6_relaxed_2_correct",
    "combined_relaxed_3_correct",
    "D_relaxed_3_correct",
    "R6_relaxed_3_correct",
    "outcome_bucket",
    "strict_blockers_for_R6",
]


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required predictions file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"No rows found in required predictions file: {path}")
    missing = [column for column in REQUIRED if column not in rows[0]]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {', '.join(missing)}")
    invalid = [row["segment_id"] for row in rows if row.get("pred_valid") != "YES"]
    if invalid:
        raise ValueError(f"{path} has invalid prediction rows: {', '.join(invalid[:10])}")
    return rows


def index_by_segment(rows, label):
    indexed = {}
    for row in rows:
        segment_id = row.get("segment_id", "").strip()
        if not segment_id:
            raise ValueError(f"Blank segment_id in {label}")
        if segment_id in indexed:
            raise ValueError(f"Duplicate segment_id in {label}: {segment_id}")
        indexed[segment_id] = row
    return indexed


def safe_div(num, den):
    return num / den if den else 0.0


def yn(value):
    return "YES" if value else "NO"


def fmt(value):
    return f"{value:.6f}"


def pct(value):
    return f"{value:.3f}"


def entity_metrics(gold_value, pred_value):
    gold = split_entity_set(gold_value)
    pred = split_entity_set(pred_value)
    inter = gold & pred
    union = gold | pred
    return gold == pred, safe_div(len(inter), len(union))


def evaluate(row):
    entity_exact, entity_j = entity_metrics(row["gold_entities"], row["pred_entities"])
    role_ok = row["gold_role"] == row["pred_role"]
    coarse5_ok = map_role(row["gold_role"], "coarse_5") == map_role(row["pred_role"], "coarse_5")
    coarse4_ok = map_role(row["gold_role"], "coarse_4") == map_role(row["pred_role"], "coarse_4")
    coarse3_ok = map_role(row["gold_role"], "coarse_3") == map_role(row["pred_role"], "coarse_3")
    status_ok = row["gold_operative_status"] == row["pred_operative_status"]
    relation_ok = row["gold_relation"] == row["pred_relation"]
    answer_ok = row["gold_answer_relevant"] == row["pred_answer_relevant"]
    strict = role_ok and status_ok and relation_ok and answer_ok and entity_exact
    relaxed_1 = role_ok and answer_ok and entity_j >= 0.5
    relaxed_2 = coarse4_ok and answer_ok and entity_j >= 0.5
    relaxed_3 = coarse3_ok and answer_ok and entity_j >= 0.5
    return {
        "role": role_ok,
        "coarse_5": coarse5_ok,
        "coarse_4": coarse4_ok,
        "coarse_3": coarse3_ok,
        "entity_exact": entity_exact,
        "entity_jaccard": entity_j,
        "status": status_ok,
        "relation": relation_ok,
        "answer": answer_ok,
        "strict": strict,
        "relaxed_1": relaxed_1,
        "relaxed_2": relaxed_2,
        "relaxed_3": relaxed_3,
    }


def score(result):
    return sum(int(result[key]) for key in ["strict", "relaxed_1", "relaxed_2", "relaxed_3"])


def strict_blockers(result):
    if result["strict"]:
        return []
    blockers = []
    if not result["role"]:
        blockers.append("role")
    if not result["entity_exact"]:
        blockers.append("entity")
    if not result["status"]:
        blockers.append("status")
    if not result["relation"]:
        blockers.append("relation")
    if not result["answer"]:
        blockers.append("answer")
    if len(blockers) > 1:
        blockers.append("multiple")
    return blockers


def classify_bucket(combined, d_result, r6, d_role, r6_role):
    guard_changed = d_role != r6_role
    blockers = strict_blockers(r6)
    if combined["strict"] and d_result["strict"] and r6["strict"]:
        return "all_strict_correct"
    if r6["strict"] and not combined["strict"] and not d_result["strict"]:
        return "R6_unique_strict_win"
    if combined["strict"] and not r6["strict"]:
        return "combined_strict_win"
    if d_result["strict"] and not r6["strict"]:
        return "D_strict_win"
    if r6["relaxed_1"] and not combined["relaxed_1"]:
        return "R6_relaxed1_gain"
    if r6["relaxed_2"] and not combined["relaxed_2"]:
        return "R6_relaxed2_gain"
    if r6["relaxed_3"] and combined["relaxed_3"] and not d_result["relaxed_3"]:
        return "R6_preserves_combined_relaxed3"
    if guard_changed and r6["role"] and not d_result["role"]:
        return "R6_role_repair_success"
    if guard_changed and d_result["role"] and not r6["role"]:
        return "R6_role_repair_failure"
    if guard_changed and r6["coarse_3"] and not d_result["coarse_3"]:
        return "R6_coarse_guard_saved_row"
    if guard_changed and d_result["coarse_3"] and not r6["coarse_3"]:
        return "R6_coarse_guard_hurt_row"
    if "multiple" in blockers:
        return "multi_field_blocks_R6"
    if "entity" in blockers:
        return "entity_blocks_R6"
    if "relation" in blockers:
        return "relation_blocks_R6"
    if "status" in blockers:
        return "status_blocks_R6"
    if "answer" in blockers:
        return "answer_blocks_R6"
    if "role" in blockers:
        return "role_blocks_R6"
    return "all_strict_wrong"


def build_rows():
    sources = {name: read_rows(path) for name, path in VARIANTS.items()}
    indexed = {name: index_by_segment(rows, name) for name, rows in sources.items()}
    segment_ids = list(indexed["combined"])
    for name in ["D", "R6"]:
        missing = [segment_id for segment_id in segment_ids if segment_id not in indexed[name]]
        if missing:
            raise ValueError(f"{name} predictions missing segment_ids: {', '.join(missing[:10])}")

    rows = []
    for segment_id in segment_ids:
        combined_row = indexed["combined"][segment_id]
        d_row = indexed["D"][segment_id]
        r6_row = indexed["R6"][segment_id]
        combined = evaluate(combined_row)
        d_result = evaluate(d_row)
        r6 = evaluate(r6_row)
        blockers = strict_blockers(r6)
        rows.append({
            "_combined": combined,
            "_D": d_result,
            "_R6": r6,
            "_text": combined_row["text"],
            "segment_id": segment_id,
            "gold_role": combined_row["gold_role"],
            "combined_role": combined_row["pred_role"],
            "D_role": d_row["pred_role"],
            "R6_role": r6_row["pred_role"],
            "combined_role_correct": yn(combined["role"]),
            "D_role_correct": yn(d_result["role"]),
            "R6_role_correct": yn(r6["role"]),
            "combined_coarse3_correct": yn(combined["coarse_3"]),
            "D_coarse3_correct": yn(d_result["coarse_3"]),
            "R6_coarse3_correct": yn(r6["coarse_3"]),
            "gold_entities": combined_row["gold_entities"],
            "combined_entities": combined_row["pred_entities"],
            "D_entities": d_row["pred_entities"],
            "R6_entities": r6_row["pred_entities"],
            "combined_entity_jaccard": fmt(combined["entity_jaccard"]),
            "D_entity_jaccard": fmt(d_result["entity_jaccard"]),
            "R6_entity_jaccard": fmt(r6["entity_jaccard"]),
            "combined_entity_exact": yn(combined["entity_exact"]),
            "D_entity_exact": yn(d_result["entity_exact"]),
            "R6_entity_exact": yn(r6["entity_exact"]),
            "gold_status": combined_row["gold_operative_status"],
            "combined_status": combined_row["pred_operative_status"],
            "D_status": d_row["pred_operative_status"],
            "R6_status": r6_row["pred_operative_status"],
            "combined_status_correct": yn(combined["status"]),
            "D_status_correct": yn(d_result["status"]),
            "R6_status_correct": yn(r6["status"]),
            "gold_relation": combined_row["gold_relation"],
            "combined_relation": combined_row["pred_relation"],
            "D_relation": d_row["pred_relation"],
            "R6_relation": r6_row["pred_relation"],
            "combined_relation_correct": yn(combined["relation"]),
            "D_relation_correct": yn(d_result["relation"]),
            "R6_relation_correct": yn(r6["relation"]),
            "gold_answer": combined_row["gold_answer_relevant"],
            "combined_answer": combined_row["pred_answer_relevant"],
            "D_answer": d_row["pred_answer_relevant"],
            "R6_answer": r6_row["pred_answer_relevant"],
            "combined_answer_correct": yn(combined["answer"]),
            "D_answer_correct": yn(d_result["answer"]),
            "R6_answer_correct": yn(r6["answer"]),
            "combined_strict_correct": yn(combined["strict"]),
            "D_strict_correct": yn(d_result["strict"]),
            "R6_strict_correct": yn(r6["strict"]),
            "combined_relaxed_1_correct": yn(combined["relaxed_1"]),
            "D_relaxed_1_correct": yn(d_result["relaxed_1"]),
            "R6_relaxed_1_correct": yn(r6["relaxed_1"]),
            "combined_relaxed_2_correct": yn(combined["relaxed_2"]),
            "D_relaxed_2_correct": yn(d_result["relaxed_2"]),
            "R6_relaxed_2_correct": yn(r6["relaxed_2"]),
            "combined_relaxed_3_correct": yn(combined["relaxed_3"]),
            "D_relaxed_3_correct": yn(d_result["relaxed_3"]),
            "R6_relaxed_3_correct": yn(r6["relaxed_3"]),
            "outcome_bucket": classify_bucket(combined, d_result, r6, d_row["pred_role"], r6_row["pred_role"]),
            "strict_blockers_for_R6": "; ".join(blockers) if blockers else "none",
        })
    return rows


def summarize_metrics(rows):
    metrics = {}
    for label, key in [("combined_v3", "_combined"), ("D", "_D"), ("R6", "_R6")]:
        n = len(rows)
        metrics[label] = {}
        for metric in ["role", "coarse_3", "entity_jaccard", "entity_exact", "status", "relation", "answer", "strict", "relaxed_1", "relaxed_2", "relaxed_3"]:
            if metric == "entity_jaccard":
                metrics[label][metric] = safe_div(sum(row[key][metric] for row in rows), n)
            else:
                metrics[label][metric] = safe_div(sum(int(row[key][metric]) for row in rows), n)
    return metrics


def role_repair_counts(rows):
    counts = Counter()
    for row in rows:
        d_result = row["_D"]
        r6 = row["_R6"]
        if row["D_role"] != row["R6_role"]:
            counts["coarse_3_guard_changed_D_role"] += 1
            if score(r6) > score(d_result):
                counts["changes_helped"] += 1
            elif score(r6) < score(d_result):
                counts["changes_hurt"] += 1
            if r6["role"] and not d_result["role"]:
                counts["changes_improved_fine_role"] += 1
            if r6["coarse_3"] and not d_result["coarse_3"] and not r6["role"]:
                counts["changes_improved_coarse3_only"] += 1
        if r6["role"] and not r6["strict"]:
            counts["R6_fine_role_correct_but_strict_fails"] += 1
    return counts


def blocker_counts(rows):
    counts = Counter()
    for row in rows:
        for blocker in strict_blockers(row["_R6"]):
            counts[blocker] += 1
    return counts


def verdict(metrics, role_counts, blockers):
    combined = metrics["combined_v3"]
    r6 = metrics["R6"]
    answers = {
        "A_relaxed1": r6["relaxed_1"] > combined["relaxed_1"],
        "B_relaxed2": r6["relaxed_2"] >= combined["relaxed_2"],
        "C_relaxed3": r6["relaxed_3"] >= combined["relaxed_3"],
        "D_strict": r6["strict"] >= combined["strict"],
        "E_fine_role": r6["role"] > combined["role"],
        "F_guard_help": role_counts["changes_helped"] > role_counts["changes_hurt"],
        "G_entity_main": blockers["entity"] >= max(blockers["relation"], blockers["status"], blockers["role"], blockers["answer"]),
        "H_relation_secondary": blockers["relation"] >= max(blockers["status"], blockers["role"], blockers["answer"]),
    }
    if all(answers[key] for key in ["A_relaxed1", "B_relaxed2", "C_relaxed3", "D_strict", "E_fine_role"]):
        final = "promote R6 as RouteMap v2 candidate"
    elif not answers["E_fine_role"] and not answers["A_relaxed1"] and not answers["D_strict"]:
        final = "reject R6 as overfit"
    else:
        final = "keep R6 provisional pending larger split"
    answers["I_overfit_evidence"] = final == "reject R6 as overfit"
    return final, answers


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def write_outputs(rows, metrics, buckets, blockers, role_counts, final, answers):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in AUDIT_FIELDS})

    lines = [
        "# Heldout R6 Candidate Audit",
        "",
        "## Audit Answers",
        "",
    ]
    answer_rows = [
        ["A. R6 beats combined_v3 on relaxed_1", yn(answers["A_relaxed1"])],
        ["B. R6 matches/beats combined_v3 on relaxed_2", yn(answers["B_relaxed2"])],
        ["C. R6 matches/beats combined_v3 on relaxed_3", yn(answers["C_relaxed3"])],
        ["D. R6 does not lose strict vs combined_v3", yn(answers["D_strict"])],
        ["E. R6 improves fine-role accuracy", yn(answers["E_fine_role"])],
        ["F. coarse_3 guard helps more than hurts", yn(answers["F_guard_help"])],
        ["G. entity exact failures remain main strict blocker", yn(answers["G_entity_main"])],
        ["H. relation remains secondary blocker", yn(answers["H_relation_secondary"])],
        ["I. evidence R6 overfit calibration set", yn(answers["I_overfit_evidence"])],
    ]
    lines.extend(md_table(["question", "answer"], answer_rows))
    lines.extend(["", "## Metrics", ""])
    metric_rows = []
    for label in ["combined_v3", "D", "R6"]:
        row = metrics[label]
        metric_rows.append([label, pct(row["role"]), pct(row["coarse_3"]), pct(row["entity_jaccard"]), pct(row["entity_exact"]), pct(row["status"]), pct(row["relation"]), pct(row["answer"]), pct(row["strict"]), pct(row["relaxed_1"]), pct(row["relaxed_2"]), pct(row["relaxed_3"])])
    lines.extend(md_table(["variant", "role", "coarse_3", "entity J", "entity exact", "status", "relation", "answer", "strict", "relaxed_1", "relaxed_2", "relaxed_3"], metric_rows))
    lines.extend(["", "## Row Buckets", ""])
    lines.extend(md_table(["outcome_bucket", "rows"], buckets.most_common()))
    lines.extend(["", "## R6 Strict Blockers", ""])
    lines.extend(md_table(["blocker", "rows"], [[key, blockers[key]] for key in ["entity", "relation", "status", "role", "answer", "multiple"]]))
    lines.extend(["", "## Role Repair Counts", ""])
    lines.extend(md_table(["measure", "rows"], [[key, role_counts[key]] for key in ["coarse_3_guard_changed_D_role", "changes_helped", "changes_hurt", "changes_improved_fine_role", "changes_improved_coarse3_only", "R6_fine_role_correct_but_strict_fails"]]))
    lines.extend([
        "",
        "## Final Verdict",
        "",
        final,
        "",
        "This audit uses the existing 84-row `expanded_test_v2` split, with no `HELDOUT2` calibration segment overlap. Predictions were generated before evaluation; gold labels were used only for scoring and audit labels.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "rows": len(rows),
        "metrics": metrics,
        "row_bucket_counts": dict(buckets),
        "R6_strict_blocker_counts": dict(blockers),
        "role_repair_counts": dict(role_counts),
        "audit_answers": answers,
        "final_verdict": final,
        "recommended_next_test": "Run the unchanged R6 stack on a larger natural-language blind split; keep expanded_test_v2 as boundary-stress evidence rather than final promotion evidence if results are mixed.",
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(metrics, buckets, blockers, role_counts, final):
    print("heldout_r6_audit")
    for label in ["combined_v3", "D", "R6"]:
        row = metrics[label]
        print(f"{label}: role={row['role']:.3f} coarse3={row['coarse_3']:.3f} entity_j={row['entity_jaccard']:.3f} entity_exact={row['entity_exact']:.3f} status={row['status']:.3f} relation={row['relation']:.3f} answer={row['answer']:.3f} strict={row['strict']:.3f} relaxed_1={row['relaxed_1']:.3f} relaxed_2={row['relaxed_2']:.3f} relaxed_3={row['relaxed_3']:.3f}")
    print("row_bucket_counts")
    for key, count in buckets.most_common():
        print(f"{key}: {count}")
    print("R6_strict_blocker_counts")
    for key, count in blockers.most_common():
        print(f"{key}: {count}")
    print("role_repair_counts")
    for key, count in role_counts.items():
        print(f"{key}: {count}")
    print(f"final_verdict={final}")
    print(f"audit_csv={OUT_CSV.relative_to(ROOT)}")
    print(f"audit_md={OUT_MD.relative_to(ROOT)}")
    print(f"audit_json={OUT_JSON.relative_to(ROOT)}")


def main():
    rows = build_rows()
    metrics = summarize_metrics(rows)
    buckets = Counter(row["outcome_bucket"] for row in rows)
    blockers = blocker_counts(rows)
    role_counts = role_repair_counts(rows)
    final, answers = verdict(metrics, role_counts, blockers)
    write_outputs(rows, metrics, buckets, blockers, role_counts, final, answers)
    print_summary(metrics, buckets, blockers, role_counts, final)


if __name__ == "__main__":
    main()
