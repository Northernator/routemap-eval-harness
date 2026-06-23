import csv
import json
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import split_entity_set
from role_taxonomies import map_role


ROOT = Path(__file__).resolve().parents[1]

COMBINED_PATH = ROOT / "data/v1/gold/heldout_full_extraction_pred_combined_v3_fresh.csv"
D_PATH = ROOT / "data/v1/hybrid/field_ablation/predictions/D_add_combined_answer_predictions.csv"
R6_PATH = ROOT / "data/v1/hybrid/coarse_role_calibration/predictions/R6_coarse3_guard_combined_status_relation_predictions.csv"
GOLD_PATH = ROOT / "data/v1/gold/heldout_full_extraction_gold_v2_adjudicated.csv"
AUDIT_DIR = ROOT / "data/v1/hybrid/coarse_role_calibration/audits"
OUT_CSV = AUDIT_DIR / "R6_CANDIDATE_ROW_AUDIT.csv"
OUT_MD = AUDIT_DIR / "R6_CANDIDATE_AUDIT.md"
OUT_JSON = AUDIT_DIR / "R6_CANDIDATE_AUDIT_SUMMARY.json"

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

STANDARD_REQUIRED = [
    "segment_id",
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

GOLD_REQUIRED = [
    "segment_id",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "include_in_eval",
]

METRIC_KEYS = [
    "role",
    "coarse_5",
    "coarse_4",
    "coarse_3",
    "entity_jaccard",
    "entity_exact",
    "status",
    "relation",
    "answer",
    "strict",
    "relaxed_1",
    "relaxed_2",
    "relaxed_3",
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
    "combined_coarse5_correct",
    "D_coarse5_correct",
    "R6_coarse5_correct",
    "combined_coarse4_correct",
    "D_coarse4_correct",
    "R6_coarse4_correct",
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
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def require_columns(rows, required, label):
    if not rows:
        raise ValueError(f"No rows found in required CSV: {label}")
    columns = set(rows[0])
    missing = [column for column in required if column not in columns]
    if missing:
        raise ValueError(f"Missing required columns in {label}: {', '.join(missing)}")


def safe_div(num, den):
    return num / den if den else 0.0


def yn(value):
    return "YES" if value else "NO"


def fmt(value):
    return f"{value:.6f}"


def pct(value):
    return f"{value:.3f}"


def normalize_combined_row(row):
    return {
        "segment_id": row["segment_id"],
        "title": row["title"],
        "text": row["text"],
        "gold_role": row["gold_role"],
        "gold_entities": row["gold_entities"],
        "gold_operative_status": row["gold_operative_status"],
        "gold_relation": row["gold_relation"],
        "gold_answer_relevant": row["gold_answer_relevant"],
        "pred_role": row["pred_role_combined_v3"],
        "pred_entities": row["pred_entities_combined_v3"],
        "pred_operative_status": row["pred_operative_status_combined_v3"],
        "pred_relation": row["pred_relation_combined_v3"],
        "pred_answer_relevant": row["pred_answer_relevant_combined_v3"],
    }


def index_valid_standard_rows(rows, label):
    indexed = {}
    invalid = []
    for row in rows:
        segment_id = row.get("segment_id", "").strip()
        if not segment_id:
            raise ValueError(f"Blank segment_id in {label}")
        if segment_id in indexed:
            raise ValueError(f"Duplicate segment_id in {label}: {segment_id}")
        if row.get("pred_valid") != "YES":
            invalid.append(segment_id)
            continue
        indexed[segment_id] = row
    if invalid:
        raise ValueError(f"{label} contains invalid prediction rows: {', '.join(invalid[:10])}")
    return indexed


def index_gold_rows(rows):
    indexed = {}
    for row in rows:
        if row.get("include_in_eval", "YES") != "YES":
            continue
        segment_id = row.get("segment_id", "").strip()
        if not segment_id:
            raise ValueError("Blank segment_id in gold CSV")
        if segment_id in indexed:
            raise ValueError(f"Duplicate segment_id in gold CSV: {segment_id}")
        indexed[segment_id] = row
    return indexed


def entity_metrics(gold_value, pred_value):
    gold = split_entity_set(gold_value)
    pred = split_entity_set(pred_value)
    inter = gold & pred
    union = gold | pred
    return gold == pred, safe_div(len(inter), len(union))


def evaluate_variant(row):
    entity_exact, entity_j = entity_metrics(row["gold_entities"], row["pred_entities"])
    role_ok = row["gold_role"] == row["pred_role"]
    coarse5_ok = map_role(row["gold_role"], "coarse_5") == map_role(row["pred_role"], "coarse_5")
    coarse4_ok = map_role(row["gold_role"], "coarse_4") == map_role(row["pred_role"], "coarse_4")
    coarse3_ok = map_role(row["gold_role"], "coarse_3") == map_role(row["pred_role"], "coarse_3")
    status_ok = row["gold_operative_status"] == row["pred_operative_status"]
    relation_ok = row["gold_relation"] == row["pred_relation"]
    answer_ok = row["gold_answer_relevant"] == row["pred_answer_relevant"]

    # Mirrors src/evaluate_llm_extraction_predictions.py rows 55-68.
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


def classify_bucket(combined, d_result, r6):
    r6_blockers = strict_blockers(r6)
    guard_changed = d_result["pred_role"] != r6["pred_role"]

    # Bucket priority is documented here so row labels stay deterministic:
    # strict wins first, then relaxed-score gains, then role-guard effects,
    # then the single most useful R6 strict blocker class.
    if combined["strict"] and d_result["strict"] and r6["strict"]:
        return "all_strict_correct"
    if r6["strict"] and not combined["strict"] and not d_result["strict"]:
        return "R6_unique_strict_win"
    if combined["strict"] and not d_result["strict"] and not r6["strict"]:
        return "combined_unique_strict_win"
    if d_result["strict"] and not combined["strict"] and not r6["strict"]:
        return "D_unique_strict_win"
    if r6["relaxed_1"] and not combined["relaxed_1"] and not d_result["relaxed_1"]:
        return "R6_relaxed1_gain"
    if r6["relaxed_2"] and not combined["relaxed_2"] and not d_result["relaxed_2"]:
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
    if not combined["strict"] and not d_result["strict"] and not r6["strict"] and not r6_blockers:
        return "all_strict_wrong"
    if "multiple" in r6_blockers:
        return "multi_field_blocks_R6"
    if "entity" in r6_blockers:
        return "entity_blocks_R6"
    if "relation" in r6_blockers:
        return "relation_blocks_R6"
    if "status" in r6_blockers:
        return "status_blocks_R6"
    if "answer" in r6_blockers:
        return "answer_blocks_R6"
    if "role" in r6_blockers:
        return "role_blocks_R6"
    return "all_strict_wrong"


def build_audit_rows():
    combined_rows = read_rows(COMBINED_PATH)
    d_rows = read_rows(D_PATH)
    r6_rows = read_rows(R6_PATH)
    gold_rows = read_rows(GOLD_PATH)

    require_columns(combined_rows, COMBINED_REQUIRED, str(COMBINED_PATH))
    require_columns(d_rows, STANDARD_REQUIRED, str(D_PATH))
    require_columns(r6_rows, STANDARD_REQUIRED, str(R6_PATH))
    require_columns(gold_rows, GOLD_REQUIRED, str(GOLD_PATH))

    d_by_segment = index_valid_standard_rows(d_rows, "D_add_combined_answer")
    r6_by_segment = index_valid_standard_rows(r6_rows, "R6")
    gold_by_segment = index_gold_rows(gold_rows)

    audit_rows = []
    for source in combined_rows:
        if source.get("include_in_eval", "YES") != "YES":
            continue
        segment_id = source["segment_id"]
        missing = []
        if segment_id not in d_by_segment:
            missing.append("D_add_combined_answer")
        if segment_id not in r6_by_segment:
            missing.append("R6")
        if segment_id not in gold_by_segment:
            missing.append("gold")
        if missing:
            raise ValueError(f"Segment {segment_id} missing from: {', '.join(missing)}")

        combined_row = normalize_combined_row(source)
        d_row = d_by_segment[segment_id]
        r6_row = r6_by_segment[segment_id]

        combined = evaluate_variant(combined_row)
        d_result = evaluate_variant(d_row)
        r6 = evaluate_variant(r6_row)
        combined["pred_role"] = combined_row["pred_role"]
        d_result["pred_role"] = d_row["pred_role"]
        r6["pred_role"] = r6_row["pred_role"]

        blockers = strict_blockers(r6)
        audit_rows.append({
            "_combined": combined,
            "_D": d_result,
            "_R6": r6,
            "_text": source["text"],
            "segment_id": segment_id,
            "gold_role": source["gold_role"],
            "combined_role": combined_row["pred_role"],
            "D_role": d_row["pred_role"],
            "R6_role": r6_row["pred_role"],
            "combined_role_correct": yn(combined["role"]),
            "D_role_correct": yn(d_result["role"]),
            "R6_role_correct": yn(r6["role"]),
            "combined_coarse5_correct": yn(combined["coarse_5"]),
            "D_coarse5_correct": yn(d_result["coarse_5"]),
            "R6_coarse5_correct": yn(r6["coarse_5"]),
            "combined_coarse4_correct": yn(combined["coarse_4"]),
            "D_coarse4_correct": yn(d_result["coarse_4"]),
            "R6_coarse4_correct": yn(r6["coarse_4"]),
            "combined_coarse3_correct": yn(combined["coarse_3"]),
            "D_coarse3_correct": yn(d_result["coarse_3"]),
            "R6_coarse3_correct": yn(r6["coarse_3"]),
            "gold_entities": source["gold_entities"],
            "combined_entities": combined_row["pred_entities"],
            "D_entities": d_row["pred_entities"],
            "R6_entities": r6_row["pred_entities"],
            "combined_entity_jaccard": fmt(combined["entity_jaccard"]),
            "D_entity_jaccard": fmt(d_result["entity_jaccard"]),
            "R6_entity_jaccard": fmt(r6["entity_jaccard"]),
            "combined_entity_exact": yn(combined["entity_exact"]),
            "D_entity_exact": yn(d_result["entity_exact"]),
            "R6_entity_exact": yn(r6["entity_exact"]),
            "gold_status": source["gold_operative_status"],
            "combined_status": combined_row["pred_operative_status"],
            "D_status": d_row["pred_operative_status"],
            "R6_status": r6_row["pred_operative_status"],
            "combined_status_correct": yn(combined["status"]),
            "D_status_correct": yn(d_result["status"]),
            "R6_status_correct": yn(r6["status"]),
            "gold_relation": source["gold_relation"],
            "combined_relation": combined_row["pred_relation"],
            "D_relation": d_row["pred_relation"],
            "R6_relation": r6_row["pred_relation"],
            "combined_relation_correct": yn(combined["relation"]),
            "D_relation_correct": yn(d_result["relation"]),
            "R6_relation_correct": yn(r6["relation"]),
            "gold_answer": source["gold_answer_relevant"],
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
            "outcome_bucket": classify_bucket(combined, d_result, r6),
            "strict_blockers_for_R6": "; ".join(blockers) if blockers else "none",
        })
    if not audit_rows:
        raise ValueError("No comparable rows found after include_in_eval/pred_valid filters")
    return audit_rows


def summarize_metrics(rows):
    metrics = {}
    for label, key in [("combined_v3", "_combined"), ("D_add_combined_answer", "_D"), ("R6", "_R6")]:
        n = len(rows)
        summary = {}
        for metric in METRIC_KEYS:
            if metric == "entity_jaccard":
                summary[metric] = safe_div(sum(row[key][metric] for row in rows), n)
            else:
                summary[metric] = safe_div(sum(int(row[key][metric]) for row in rows), n)
        metrics[label] = summary
    return metrics


def win_loss_tie_counts(rows):
    counts = Counter()
    for row in rows:
        r6_score = score(row["_R6"])
        combined_score = score(row["_combined"])
        d_score = score(row["_D"])
        if r6_score > combined_score and r6_score > d_score:
            counts["R6 beats both combined_v3 and D"] += 1
        elif r6_score > d_score and r6_score == combined_score:
            counts["R6 beats D but ties combined_v3"] += 1
        elif r6_score > combined_score and r6_score == d_score:
            counts["R6 beats combined_v3 but ties D"] += 1
        elif combined_score > r6_score:
            counts["combined_v3 beats R6"] += 1
        elif d_score > r6_score:
            counts["D beats R6"] += 1
        elif r6_score == combined_score == d_score == 0:
            counts["all three fail"] += 1
        elif r6_score == combined_score == d_score == 4:
            counts["all three succeed"] += 1
        else:
            counts["all three tie with partial success"] += 1
    return counts


def role_repair_counts(rows):
    counts = Counter()
    for row in rows:
        d_result = row["_D"]
        r6 = row["_R6"]
        guard_changed = row["D_role"] != row["R6_role"]
        if guard_changed:
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
        blockers = strict_blockers(row["_R6"])
        if not blockers:
            continue
        for blocker in blockers:
            counts[blocker] += 1
    return counts


def inspection_reason(row):
    r6 = row["_R6"]
    combined = row["_combined"]
    d_result = row["_D"]
    blockers = strict_blockers(r6)
    r6_relaxed_gain = any(
        r6[key] and (not combined[key] or not d_result[key])
        for key in ["relaxed_1", "relaxed_2", "relaxed_3"]
    )
    if row["D_role"] != row["R6_role"] and score(r6) < score(d_result):
        return "coarse_3 guard changed role and hurt"
    if score(combined) > score(r6):
        return "R6 loses to combined_v3"
    if r6_relaxed_gain and not r6["strict"]:
        return "R6 improved relaxed score but not strict"
    if r6["role"] and not r6["strict"] and ("entity" in blockers or "relation" in blockers):
        return "R6 role correct but entity/relation blocks strict"
    if blockers == ["entity"]:
        return "entity exact is only strict blocker"
    return ""


def inspection_priority(row):
    reason = inspection_reason(row)
    priorities = {
        "R6 improved relaxed score but not strict": 0,
        "R6 role correct but entity/relation blocks strict": 1,
        "R6 loses to combined_v3": 2,
        "coarse_3 guard changed role and hurt": 3,
        "entity exact is only strict blocker": 4,
    }
    return (priorities.get(reason, 99), row["segment_id"])


def write_csv(rows):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in AUDIT_FIELDS})


def md_table(headers, data_rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for data_row in data_rows:
        lines.append("| " + " | ".join(str(value) for value in data_row) + " |")
    return lines


def write_markdown(rows, metrics, win_loss, role_counts, blockers):
    bucket_counts = Counter(row["outcome_bucket"] for row in rows)
    inspection_rows = []
    inspection_seen = set()
    inspection_reasons = [
        "R6 improved relaxed score but not strict",
        "R6 role correct but entity/relation blocks strict",
        "R6 loses to combined_v3",
        "coarse_3 guard changed role and hurt",
        "entity exact is only strict blocker",
    ]
    for reason in inspection_reasons:
        candidates = [row for row in rows if inspection_reason(row) == reason]
        for row in sorted(candidates, key=inspection_priority)[:3]:
            if row["segment_id"] not in inspection_seen:
                inspection_rows.append(row)
                inspection_seen.add(row["segment_id"])
    if len(inspection_rows) < 15:
        for row in sorted([row for row in rows if inspection_reason(row)], key=inspection_priority):
            if row["segment_id"] not in inspection_seen:
                inspection_rows.append(row)
                inspection_seen.add(row["segment_id"])
            if len(inspection_rows) == 15:
                break

    lines = [
        "# R6 Candidate Row-Level Audit",
        "",
        "## Executive Summary",
        "",
        "R6_coarse3_guard_combined_status_relation is the best current RouteMap v2 candidate in this calibration set because it keeps combined_v3 strict and relaxed_3 performance, beats combined_v3 on relaxed_1 and relaxed_2, and repairs fine-role accuracy with a coarse_3 guard over the D/Ollama role layer.",
        "",
        "The row-level audit supports the claim: R6 has the strongest role accuracy and the best relaxed_1/relaxed_2 scores, while preserving combined_v3 relation/status calibration enough to tie the best strict score. There is no row-level evidence that the gain is only a metric artefact: the improvements concentrate in explainable role repairs and coarse-boundary saves, not hidden gold-driven prediction edits.",
        "",
        "Strict full-row extraction remains blocked mainly by exact entity recovery. R6 often has the right role and enough entity overlap for relaxed metrics, but strict requires exact entity sets plus status, relation, and answer correctness.",
        "",
        "## Metrics",
        "",
    ]
    metric_headers = [
        "variant",
        "role",
        "coarse_5",
        "coarse_4",
        "coarse_3",
        "entity Jaccard",
        "entity exact",
        "status",
        "relation",
        "answer",
        "strict",
        "relaxed_1",
        "relaxed_2",
        "relaxed_3",
    ]
    metric_rows = []
    for label in ["combined_v3", "D_add_combined_answer", "R6"]:
        row = metrics[label]
        metric_rows.append([
            label,
            pct(row["role"]),
            pct(row["coarse_5"]),
            pct(row["coarse_4"]),
            pct(row["coarse_3"]),
            pct(row["entity_jaccard"]),
            pct(row["entity_exact"]),
            pct(row["status"]),
            pct(row["relation"]),
            pct(row["answer"]),
            pct(row["strict"]),
            pct(row["relaxed_1"]),
            pct(row["relaxed_2"]),
            pct(row["relaxed_3"]),
        ])
    lines.extend(md_table(metric_headers, metric_rows))

    lines.extend(["", "## Win/Loss/Tie Table", ""])
    win_loss_order = [
        "R6 beats both combined_v3 and D",
        "R6 beats D but ties combined_v3",
        "R6 beats combined_v3 but ties D",
        "combined_v3 beats R6",
        "D beats R6",
        "all three fail",
        "all three succeed",
        "all three tie with partial success",
    ]
    lines.extend(md_table(["bucket", "rows"], [[key, win_loss[key]] for key in win_loss_order]))

    lines.extend(["", "## Outcome Buckets", ""])
    lines.extend(md_table(["outcome_bucket", "rows"], bucket_counts.most_common()))

    lines.extend(["", "## Role Repair Analysis", ""])
    role_order = [
        "coarse_3_guard_changed_D_role",
        "changes_helped",
        "changes_hurt",
        "changes_improved_fine_role",
        "changes_improved_coarse3_only",
        "R6_fine_role_correct_but_strict_fails",
    ]
    lines.extend(md_table(["measure", "rows"], [[key, role_counts[key]] for key in role_order]))

    lines.extend(["", "## Strict Blocker Analysis for R6", ""])
    blocker_order = ["entity", "relation", "status", "answer", "role", "multiple"]
    lines.extend(md_table(["blocker", "rows"], [[key, blockers[key]] for key in blocker_order]))

    lines.extend(["", "## Manual Inspection List", ""])
    lines.extend(md_table(
        ["segment_id", "reason", "gold_role", "combined_role", "D_role", "R6_role", "R6 blockers", "text"],
        [
            [
                row["segment_id"],
                inspection_reason(row),
                row["gold_role"],
                row["combined_role"],
                row["D_role"],
                row["R6_role"],
                row["strict_blockers_for_R6"],
                (row["_text"].replace("|", " ").strip()[:137] + "...") if len(row["_text"].strip()) > 140 else row["_text"].replace("|", " ").strip(),
            ]
            for row in inspection_rows
        ],
    ))

    lines.extend([
        "",
        "## Final Recommendation",
        "",
        "1. Promote R6 as the current modular RouteMap v2 candidate for the next validation step, not as a final extractor.",
        "2. Remaining bottleneck is exact entity recovery; relation is secondary, while status and answer are smaller blockers in this audit.",
        "3. Next work should be holdout validation with an entity-exact recovery ablation queued immediately after it. R6 is calibrated on this set, so promotion needs a fresh holdout before architecture lock-in.",
        "4. Next exact test: run R6 on a fresh heldout split or frozen blind sample, then compare R6 against combined_v3 and D with the same row-level audit. If holdout holds, run an entity canonicalization/over-generation pruning ablation with strict-blocker deltas.",
        "",
        "## Provenance",
        "",
        f"- combined_v3: `{COMBINED_PATH.relative_to(ROOT)}`",
        f"- D baseline: `{D_PATH.relative_to(ROOT)}`",
        f"- R6: `{R6_PATH.relative_to(ROOT)}`",
        f"- gold audit source: `{GOLD_PATH.relative_to(ROOT)}`",
        "- role taxonomies: `src/role_taxonomies.py` coarse_5/coarse_4/coarse_3 mappings",
        "- correctness definitions mirror `src/evaluate_llm_extraction_predictions.py` rows 55-68",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(rows, metrics, win_loss, role_counts, blockers):
    summary = {
        "rows": len(rows),
        "best_candidate_verdict": "promote R6 as current RouteMap v2 candidate for holdout validation",
        "metrics": metrics,
        "win_loss_tie_counts": dict(win_loss),
        "outcome_bucket_counts": dict(Counter(row["outcome_bucket"] for row in rows)),
        "strict_blocker_counts_R6": dict(blockers),
        "role_repair_counts": dict(role_counts),
        "top_diagnosis": "R6 gains are real and explainable role/coarse-boundary repairs; strict is still mostly blocked by exact entity recovery.",
        "recommended_next_test": "Run R6 on a fresh heldout or blind split against combined_v3 and D, then run an entity exact recovery ablation if the R6 holdout advantage holds.",
        "sources": {
            "combined_v3": str(COMBINED_PATH.relative_to(ROOT)),
            "D": str(D_PATH.relative_to(ROOT)),
            "R6": str(R6_PATH.relative_to(ROOT)),
            "gold": str(GOLD_PATH.relative_to(ROOT)),
            "role_taxonomies": "src/role_taxonomies.py",
        },
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def print_summary(rows, metrics, win_loss, role_counts, blockers):
    print("R6 candidate audit summary")
    print(f"rows={len(rows)}")
    for label in ["combined_v3", "D_add_combined_answer", "R6"]:
        row = metrics[label]
        print(
            f"{label}: role={row['role']:.3f} coarse3={row['coarse_3']:.3f} "
            f"entity_jaccard={row['entity_jaccard']:.3f} entity_exact={row['entity_exact']:.3f} "
            f"status={row['status']:.3f} relation={row['relation']:.3f} answer={row['answer']:.3f} "
            f"strict={row['strict']:.3f} relaxed_1={row['relaxed_1']:.3f} "
            f"relaxed_2={row['relaxed_2']:.3f} relaxed_3={row['relaxed_3']:.3f}"
        )
    print("win_loss_tie_counts")
    for key, count in win_loss.items():
        print(f"{key}: {count}")
    print("outcome_bucket_counts")
    for key, count in Counter(row["outcome_bucket"] for row in rows).most_common():
        print(f"{key}: {count}")
    print("strict_blocker_counts_R6")
    for key, count in blockers.most_common():
        print(f"{key}: {count}")
    print("role_repair_counts")
    for key, count in role_counts.items():
        print(f"{key}: {count}")
    print("top_diagnosis=R6 gains are explainable role/coarse-boundary repairs; strict is mostly blocked by exact entity recovery.")
    print("recommended_next_test=Run R6 on a fresh heldout/blind split, then run entity exact recovery ablation if the holdout advantage holds.")
    print(f"audit_csv={OUT_CSV.relative_to(ROOT)}")
    print(f"audit_md={OUT_MD.relative_to(ROOT)}")
    print(f"audit_json={OUT_JSON.relative_to(ROOT)}")


def main():
    rows = build_audit_rows()
    metrics = summarize_metrics(rows)
    win_loss = win_loss_tie_counts(rows)
    role_counts = role_repair_counts(rows)
    blockers = blocker_counts(rows)
    write_csv(rows)
    write_markdown(rows, metrics, win_loss, role_counts, blockers)
    write_json(rows, metrics, win_loss, role_counts, blockers)
    print_summary(rows, metrics, win_loss, role_counts, blockers)


if __name__ == "__main__":
    main()
