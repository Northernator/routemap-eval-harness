import csv
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import split_entity_set
from role_taxonomies import map_role


COMBINED_PATH = Path("data/v1/gold/heldout_full_extraction_pred_combined_v3_fresh.csv")
D_PATH = Path("data/v1/hybrid/field_ablation/predictions/D_add_combined_answer_predictions.csv")
OUT_DIR = Path("data/v1/hybrid/field_ablation/audits")
OUT_CSV = OUT_DIR / "combined_v3_vs_D_add_combined_answer_row_audit.csv"
OUT_MD = OUT_DIR / "combined_v3_vs_D_add_combined_answer_audit.md"

COMBINED_REQUIRED = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "include_in_eval",
    "pred_role_combined_v3",
    "pred_entities_combined_v3",
    "pred_operative_status_combined_v3",
    "pred_relation_combined_v3",
    "pred_answer_relevant_combined_v3",
]

D_REQUIRED = [
    "segment_id",
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
    "combined_role_correct",
    "D_role_correct",
    "gold_entities",
    "combined_entities",
    "D_entities",
    "combined_entity_jaccard",
    "D_entity_jaccard",
    "combined_entity_correct",
    "D_entity_correct",
    "gold_status",
    "combined_status",
    "D_status",
    "combined_status_correct",
    "D_status_correct",
    "gold_relation",
    "combined_relation",
    "D_relation",
    "combined_relation_correct",
    "D_relation_correct",
    "gold_answer",
    "combined_answer",
    "D_answer",
    "combined_answer_correct",
    "D_answer_correct",
    "combined_strict_correct",
    "D_strict_correct",
    "combined_relaxed_1_correct",
    "D_relaxed_1_correct",
    "combined_relaxed_2_correct",
    "D_relaxed_2_correct",
    "combined_relaxed_3_correct",
    "D_relaxed_3_correct",
    "outcome_bucket",
]


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def require_columns(rows, required, label):
    if not rows:
        raise ValueError(f"{label} has no rows")
    missing = [column for column in required if column not in rows[0]]
    if missing:
        raise ValueError(f"{label} missing columns: {', '.join(missing)}")


def index_by_segment(rows, label):
    indexed = {}
    for row in rows:
        segment_id = row.get("segment_id", "")
        if not segment_id:
            raise ValueError(f"{label} row missing segment_id")
        if segment_id in indexed:
            raise ValueError(f"{label} duplicate segment_id: {segment_id}")
        indexed[segment_id] = row
    return indexed


def safe_div(num, den):
    return num / den if den else 0.0


def entity_metrics(gold_value, pred_value):
    gold = split_entity_set(gold_value)
    pred = split_entity_set(pred_value)
    inter = gold & pred
    union = gold | pred
    return gold == pred, safe_div(len(inter), len(union))


def evaluate_variant(row, role, entities, status, relation, answer):
    entity_exact, entity_j = entity_metrics(row["gold_entities"], entities)
    role_ok = row["gold_role"] == role
    coarse4_ok = map_role(row["gold_role"], "coarse_4") == map_role(role, "coarse_4")
    coarse3_ok = map_role(row["gold_role"], "coarse_3") == map_role(role, "coarse_3")
    status_ok = row["gold_operative_status"] == status
    relation_ok = row["gold_relation"] == relation
    answer_ok = row["gold_answer_relevant"] == answer
    strict = role_ok and entity_exact and status_ok and relation_ok and answer_ok
    relaxed_1 = role_ok and answer_ok and entity_j >= 0.5
    relaxed_2 = coarse4_ok and answer_ok and entity_j >= 0.5
    relaxed_3 = coarse3_ok and answer_ok and entity_j >= 0.5
    return {
        "role": role_ok,
        "coarse4": coarse4_ok,
        "coarse3": coarse3_ok,
        "entity_exact": entity_exact,
        "entity_j": entity_j,
        "status": status_ok,
        "relation": relation_ok,
        "answer": answer_ok,
        "strict": strict,
        "relaxed_1": relaxed_1,
        "relaxed_2": relaxed_2,
        "relaxed_3": relaxed_3,
    }


def yn(value):
    return "YES" if value else "NO"


def fmt(value):
    return f"{value:.6f}"


def metric_score(result):
    return sum(int(result[key]) for key in ["strict", "relaxed_1", "relaxed_2", "relaxed_3"])


def classify_bucket(combined, d_result):
    if combined["strict"] and d_result["strict"]:
        return "both_strict_correct"
    if combined["strict"] and not d_result["strict"]:
        return "combined_strict_only"
    if d_result["strict"] and not combined["strict"]:
        return "D_strict_only"
    if d_result["relaxed_1"] and not combined["relaxed_1"]:
        return "D_relaxed1_only"
    if (combined["relaxed_2"] and not d_result["relaxed_2"]) or (combined["relaxed_3"] and not d_result["relaxed_3"]):
        return "combined_relaxed2_or_3_only"
    if d_result["role"] and not combined["role"] and not d_result["strict"]:
        return "D_role_gain_but_other_fields_fail"
    if (not combined["role"]) and (combined["relaxed_2"] or combined["relaxed_3"]):
        return "combined_role_wrong_but_other_fields_compensate"
    if d_result["role"] and d_result["answer"] and d_result["entity_j"] < 0.5:
        return "entity_blocks_D"
    if d_result["role"] and d_result["entity_exact"] and d_result["answer"] and d_result["relation"] and not d_result["status"]:
        return "status_blocks_D"
    if d_result["role"] and d_result["entity_exact"] and d_result["answer"] and d_result["status"] and not d_result["relation"]:
        return "relation_blocks_D"
    if d_result["role"] and d_result["entity_j"] >= 0.5 and not d_result["answer"]:
        return "answer_blocks_D"
    return "both_strict_wrong"


def audit_rows():
    combined_rows = read_rows(COMBINED_PATH)
    d_rows = read_rows(D_PATH)
    require_columns(combined_rows, COMBINED_REQUIRED, str(COMBINED_PATH))
    require_columns(d_rows, D_REQUIRED, str(D_PATH))
    d_by_segment = index_by_segment(d_rows, "D predictions")

    output = []
    for combined_row in combined_rows:
        if combined_row.get("include_in_eval", "YES") != "YES":
            continue
        segment_id = combined_row["segment_id"]
        if segment_id not in d_by_segment:
            raise ValueError(f"D predictions missing segment_id: {segment_id}")
        d_row = d_by_segment[segment_id]
        if d_row.get("pred_valid") != "YES":
            raise ValueError(f"D prediction is not valid for segment_id: {segment_id}")

        combined_result = evaluate_variant(
            combined_row,
            combined_row["pred_role_combined_v3"],
            combined_row["pred_entities_combined_v3"],
            combined_row["pred_operative_status_combined_v3"],
            combined_row["pred_relation_combined_v3"],
            combined_row["pred_answer_relevant_combined_v3"],
        )
        d_result = evaluate_variant(
            combined_row,
            d_row["pred_role"],
            d_row["pred_entities"],
            d_row["pred_operative_status"],
            d_row["pred_relation"],
            d_row["pred_answer_relevant"],
        )

        output.append({
            "segment_id": segment_id,
            "gold_role": combined_row["gold_role"],
            "combined_role": combined_row["pred_role_combined_v3"],
            "D_role": d_row["pred_role"],
            "combined_role_correct": yn(combined_result["role"]),
            "D_role_correct": yn(d_result["role"]),
            "gold_entities": combined_row["gold_entities"],
            "combined_entities": combined_row["pred_entities_combined_v3"],
            "D_entities": d_row["pred_entities"],
            "combined_entity_jaccard": fmt(combined_result["entity_j"]),
            "D_entity_jaccard": fmt(d_result["entity_j"]),
            "combined_entity_correct": yn(combined_result["entity_exact"]),
            "D_entity_correct": yn(d_result["entity_exact"]),
            "gold_status": combined_row["gold_operative_status"],
            "combined_status": combined_row["pred_operative_status_combined_v3"],
            "D_status": d_row["pred_operative_status"],
            "combined_status_correct": yn(combined_result["status"]),
            "D_status_correct": yn(d_result["status"]),
            "gold_relation": combined_row["gold_relation"],
            "combined_relation": combined_row["pred_relation_combined_v3"],
            "D_relation": d_row["pred_relation"],
            "combined_relation_correct": yn(combined_result["relation"]),
            "D_relation_correct": yn(d_result["relation"]),
            "gold_answer": combined_row["gold_answer_relevant"],
            "combined_answer": combined_row["pred_answer_relevant_combined_v3"],
            "D_answer": d_row["pred_answer_relevant"],
            "combined_answer_correct": yn(combined_result["answer"]),
            "D_answer_correct": yn(d_result["answer"]),
            "combined_strict_correct": yn(combined_result["strict"]),
            "D_strict_correct": yn(d_result["strict"]),
            "combined_relaxed_1_correct": yn(combined_result["relaxed_1"]),
            "D_relaxed_1_correct": yn(d_result["relaxed_1"]),
            "combined_relaxed_2_correct": yn(combined_result["relaxed_2"]),
            "D_relaxed_2_correct": yn(d_result["relaxed_2"]),
            "combined_relaxed_3_correct": yn(combined_result["relaxed_3"]),
            "D_relaxed_3_correct": yn(d_result["relaxed_3"]),
            "outcome_bucket": classify_bucket(combined_result, d_result),
            "_combined": combined_result,
            "_D": d_result,
            "_title": combined_row["title"],
            "_text": combined_row["text"],
        })
    return output


def summarize(rows):
    metrics = {}
    for label, key in [("combined", "_combined"), ("D", "_D")]:
        n = len(rows)
        metrics[label] = {
            "strict": safe_div(sum(row[key]["strict"] for row in rows), n),
            "relaxed_1": safe_div(sum(row[key]["relaxed_1"] for row in rows), n),
            "relaxed_2": safe_div(sum(row[key]["relaxed_2"] for row in rows), n),
            "relaxed_3": safe_div(sum(row[key]["relaxed_3"] for row in rows), n),
            "role": safe_div(sum(row[key]["role"] for row in rows), n),
            "entity_j": safe_div(sum(row[key]["entity_j"] for row in rows), n),
            "status": safe_div(sum(row[key]["status"] for row in rows), n),
            "relation": safe_div(sum(row[key]["relation"] for row in rows), n),
            "answer": safe_div(sum(row[key]["answer"] for row in rows), n),
        }
    return metrics


def blocker_counts(rows, loser_key, winner_key):
    blockers = Counter()
    for row in rows:
        loser = row[loser_key]
        winner = row[winner_key]
        if metric_score(loser) >= metric_score(winner):
            continue
        missing = []
        if not loser["role"]:
            missing.append("role")
        if loser["entity_j"] < 0.5:
            missing.append("entity")
        if not loser["status"]:
            missing.append("status")
        if not loser["relation"]:
            missing.append("relation")
        if not loser["answer"]:
            missing.append("answer")
        for item in missing:
            blockers[item] += 1
        if len(missing) > 1:
            blockers["multiple_field"] += 1
    return blockers


def inspection_priority(row):
    combined = row["_combined"]
    d_result = row["_D"]
    if d_result["role"] and not d_result["strict"] and (not d_result["relaxed_2"] or not d_result["relaxed_3"]):
        return 0
    if (not combined["role"]) and (combined["relaxed_2"] or combined["relaxed_3"]):
        return 1
    if abs(d_result["entity_j"] - combined["entity_j"]) > 0.001:
        return 2
    if d_result["role"] and d_result["entity_exact"] and d_result["answer"] and (not d_result["status"] or not d_result["relation"]):
        return 3
    return 9


def write_csv(rows):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in AUDIT_FIELDS})


def write_markdown(rows, metrics):
    bucket_counts = Counter(row["outcome_bucket"] for row in rows)
    combined_better = [row for row in rows if metric_score(row["_combined"]) > metric_score(row["_D"])]
    d_better = [row for row in rows if metric_score(row["_D"]) > metric_score(row["_combined"])]
    tie_correct = [row for row in rows if metric_score(row["_combined"]) == metric_score(row["_D"]) and metric_score(row["_D"]) > 0]
    tie_wrong = [row for row in rows if metric_score(row["_combined"]) == metric_score(row["_D"]) and metric_score(row["_D"]) == 0]
    d_loser_blockers = blocker_counts(rows, "_D", "_combined")
    combined_loser_blockers = blocker_counts(rows, "_combined", "_D")

    top_rows = sorted(rows, key=lambda row: (inspection_priority(row), row["segment_id"]))[:10]

    lines = [
        "# Strict Row Failure Audit: combined_v3 vs D_add_combined_answer",
        "",
        "## Summary",
        "",
        "| variant | role | entity_jaccard | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label in ["combined", "D"]:
        row = metrics[label]
        lines.append(
            f"| {label} | {row['role']:.3f} | {row['entity_j']:.3f} | {row['status']:.3f} | {row['relation']:.3f} | {row['answer']:.3f} | {row['strict']:.3f} | {row['relaxed_1']:.3f} | {row['relaxed_2']:.3f} | {row['relaxed_3']:.3f} |"
        )
    lines.extend([
        "",
        "## Win/Loss",
        "",
        "| bucket | rows |",
        "|---|---:|",
        f"| D better | {len(d_better)} |",
        f"| combined_v3 better | {len(combined_better)} |",
        f"| both tie with at least one success | {len(tie_correct)} |",
        f"| both tie wrong | {len(tie_wrong)} |",
        "",
        "## Outcome Buckets",
        "",
        "| outcome_bucket | rows |",
        "|---|---:|",
    ])
    for bucket, count in bucket_counts.most_common():
        lines.append(f"| {bucket} | {count} |")

    lines.extend(["", "## D Loses To Combined: Field Blockers", "", "| blocker | rows |", "|---|---:|"])
    for blocker in ["role", "entity", "status", "relation", "answer", "multiple_field"]:
        lines.append(f"| {blocker} | {d_loser_blockers[blocker]} |")

    lines.extend(["", "## Combined Loses To D: Field Blockers", "", "| blocker | rows |", "|---|---:|"])
    for blocker in ["role", "entity", "status", "relation", "answer", "multiple_field"]:
        lines.append(f"| {blocker} | {combined_loser_blockers[blocker]} |")

    lines.extend([
        "",
        "## Top Rows To Inspect",
        "",
        "| segment_id | gold_role | combined_role | D_role | combined_r1/r2/r3 | D_r1/r2/r3 | bucket | text |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for row in top_rows:
        combined_flags = f"{row['combined_relaxed_1_correct']}/{row['combined_relaxed_2_correct']}/{row['combined_relaxed_3_correct']}"
        d_flags = f"{row['D_relaxed_1_correct']}/{row['D_relaxed_2_correct']}/{row['D_relaxed_3_correct']}"
        text = row["_text"].replace("|", " ").strip()
        if len(text) > 140:
            text = text[:137] + "..."
        lines.append(
            f"| {row['segment_id']} | {row['gold_role']} | {row['combined_role']} | {row['D_role']} | {combined_flags} | {d_flags} | {row['outcome_bucket']} | {text} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "1. Ollama role gains land on some relaxed_1 rows: D has higher fine-role accuracy and converts rows where combined_v3 misses the exact fine role.",
        "2. D beats combined_v3 on relaxed_1 because relaxed_1 requires exact fine role, answer correctness, and entity Jaccard >= 0.5; D keeps Ollama's stronger fine-role signal and borrows combined_v3 answer relevance plus ontology entities.",
        "3. D loses on relaxed_2 and relaxed_3 because combined_v3's role errors often remain inside the correct coarse_4/coarse_3 buckets, while Ollama's wrong roles more often cross coarse boundaries.",
        "4. Relation/status are strict-row blockers, but they are not relaxed-score blockers under the current definitions; strict still needs exact entities plus status and relation.",
        "5. RouteMap v2 should test a modular extractor with Ollama-style fine-role routing, ontology entities, deterministic answer relevance, and a separate relation/status calibration layer evaluated with strict-row audits.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(rows, metrics):
    print("summary")
    for label in ["combined", "D"]:
        row = metrics[label]
        print(
            f"{label}: strict={row['strict']:.3f} relaxed_1={row['relaxed_1']:.3f} "
            f"relaxed_2={row['relaxed_2']:.3f} relaxed_3={row['relaxed_3']:.3f}"
        )
    print("outcome_buckets")
    for bucket, count in Counter(row["outcome_bucket"] for row in rows).most_common():
        print(f"{bucket}: {count}")
    print(f"audit_csv={OUT_CSV}")
    print(f"audit_md={OUT_MD}")


def main():
    rows = audit_rows()
    metrics = summarize(rows)
    write_csv(rows)
    write_markdown(rows, metrics)
    print_summary(rows, metrics)


if __name__ == "__main__":
    main()
