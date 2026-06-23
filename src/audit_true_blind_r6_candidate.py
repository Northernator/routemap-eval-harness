import csv
import json
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import split_entity_set
from role_taxonomies import map_role


ROOT = Path(__file__).resolve().parents[1]
TRUE_BLIND_ROOT = ROOT / "data/v1/true_blind_natural_language"
PRED_DIR = TRUE_BLIND_ROOT / "predictions"
AUDIT_DIR = TRUE_BLIND_ROOT / "audits"
OUT_CSV = AUDIT_DIR / "TRUE_BLIND_R6_ROW_AUDIT.csv"
OUT_MD = AUDIT_DIR / "TRUE_BLIND_R6_AUDIT.md"
OUT_JSON = AUDIT_DIR / "TRUE_BLIND_R6_AUDIT_SUMMARY.json"

VARIANTS = {
    "combined_v3": PRED_DIR / "combined_v3_true_blind_predictions.csv",
    "D": PRED_DIR / "D_true_blind_predictions.csv",
    "R6": PRED_DIR / "R6_true_blind_predictions.csv",
}

REQUIRED = [
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

METRICS = [
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
    "gold_coarse_5",
    "gold_coarse_4",
    "gold_coarse_3",
    "gold_entities",
    "gold_status",
    "gold_relation",
    "gold_answer",
]

for variant in ["combined_v3", "D", "R6"]:
    AUDIT_FIELDS.extend([
        f"{variant}_role",
        f"{variant}_role_correct",
        f"{variant}_coarse_5_correct",
        f"{variant}_coarse_4_correct",
        f"{variant}_coarse_3_correct",
        f"{variant}_entities",
        f"{variant}_entity_jaccard",
        f"{variant}_entity_exact",
        f"{variant}_status",
        f"{variant}_status_correct",
        f"{variant}_relation",
        f"{variant}_relation_correct",
        f"{variant}_answer",
        f"{variant}_answer_correct",
        f"{variant}_strict_correct",
        f"{variant}_relaxed_1_correct",
        f"{variant}_relaxed_2_correct",
        f"{variant}_relaxed_3_correct",
    ])

AUDIT_FIELDS.extend(["R6_strict_blockers", "outcome_bucket"])


def yn(value):
    return "YES" if value else "NO"


def safe_div(num, den):
    return num / den if den else 0.0


def pct(value):
    return f"{value:.3f}"


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing predictions file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"No rows found in predictions file: {path}")
    missing = [column for column in REQUIRED if column not in rows[0]]
    if missing:
        raise ValueError(f"Missing columns in {path}: {', '.join(missing)}")
    invalid = [row["segment_id"] for row in rows if row.get("pred_valid") != "YES"]
    if invalid:
        raise ValueError(f"Invalid prediction rows in {path}: {', '.join(invalid[:10])}")
    return rows


def index_rows(rows, label):
    indexed = {}
    for row in rows:
        segment_id = row.get("segment_id", "").strip()
        if not segment_id:
            raise ValueError(f"Blank segment_id in {label}")
        if segment_id in indexed:
            raise ValueError(f"Duplicate segment_id in {label}: {segment_id}")
        indexed[segment_id] = row
    return indexed


def entity_metrics(gold_value, pred_value):
    gold = split_entity_set(gold_value)
    pred = split_entity_set(pred_value)
    union = gold | pred
    return gold == pred, safe_div(len(gold & pred), len(union))


def score_row(row):
    entity_exact, entity_jaccard = entity_metrics(row["gold_entities"], row["pred_entities"])
    role = row["gold_role"] == row["pred_role"]
    coarse_5 = map_role(row["gold_role"], "coarse_5") == map_role(row["pred_role"], "coarse_5")
    coarse_4 = map_role(row["gold_role"], "coarse_4") == map_role(row["pred_role"], "coarse_4")
    coarse_3 = map_role(row["gold_role"], "coarse_3") == map_role(row["pred_role"], "coarse_3")
    status = row["gold_operative_status"] == row["pred_operative_status"]
    relation = row["gold_relation"] == row["pred_relation"]
    answer = row["gold_answer_relevant"] == row["pred_answer_relevant"]
    strict = role and entity_exact and status and relation and answer
    return {
        "role": role,
        "coarse_5": coarse_5,
        "coarse_4": coarse_4,
        "coarse_3": coarse_3,
        "entity_jaccard": entity_jaccard,
        "entity_exact": entity_exact,
        "status": status,
        "relation": relation,
        "answer": answer,
        "strict": strict,
        "relaxed_1": role and answer and entity_jaccard >= 0.5,
        "relaxed_2": coarse_4 and answer and entity_jaccard >= 0.5,
        "relaxed_3": coarse_3 and answer and entity_jaccard >= 0.5,
    }


def strict_blockers(score):
    if score["strict"]:
        return []
    blockers = []
    for key, label in [
        ("role", "role"),
        ("entity_exact", "entity"),
        ("status", "status"),
        ("relation", "relation"),
        ("answer", "answer"),
    ]:
        if not score[key]:
            blockers.append(label)
    if len(blockers) > 1:
        blockers.append("multiple")
    return blockers


def score_total(score):
    return sum(int(score[key]) for key in ["strict", "relaxed_1", "relaxed_2", "relaxed_3"])


def classify(scores, rows):
    combined = scores["combined_v3"]
    d_score = scores["D"]
    r6 = scores["R6"]
    guard_changed = rows["D"]["pred_role"] != rows["R6"]["pred_role"]
    if r6["strict"] and not combined["strict"] and not d_score["strict"]:
        return "R6_unique_strict_win"
    if combined["strict"] and not r6["strict"]:
        return "combined_strict_win"
    if d_score["strict"] and not r6["strict"]:
        return "D_strict_win"
    if r6["relaxed_1"] and not combined["relaxed_1"]:
        return "R6_relaxed1_gain"
    if r6["relaxed_2"] and not combined["relaxed_2"]:
        return "R6_relaxed2_gain"
    if guard_changed and r6["role"] and not d_score["role"]:
        return "R6_role_repair_success"
    if guard_changed and d_score["role"] and not r6["role"]:
        return "R6_role_repair_failure"
    blockers = strict_blockers(r6)
    if "multiple" in blockers:
        return "multi_field_blocks_R6"
    for blocker in ["entity", "relation", "status", "answer", "role"]:
        if blocker in blockers:
            return f"{blocker}_blocks_R6"
    return "all_strict_correct" if r6["strict"] else "all_strict_wrong"


def build_rows():
    indexed = {name: index_rows(read_rows(path), name) for name, path in VARIANTS.items()}
    segment_ids = list(indexed["combined_v3"])
    for name in ["D", "R6"]:
        missing = [segment_id for segment_id in segment_ids if segment_id not in indexed[name]]
        if missing:
            raise ValueError(f"{name} missing segment_ids: {', '.join(missing[:10])}")
    audit_rows = []
    for segment_id in segment_ids:
        pred_rows = {name: indexed[name][segment_id] for name in ["combined_v3", "D", "R6"]}
        scores = {name: score_row(row) for name, row in pred_rows.items()}
        base = pred_rows["combined_v3"]
        out = {
            "_scores": scores,
            "segment_id": segment_id,
            "gold_role": base["gold_role"],
            "gold_coarse_5": map_role(base["gold_role"], "coarse_5"),
            "gold_coarse_4": map_role(base["gold_role"], "coarse_4"),
            "gold_coarse_3": map_role(base["gold_role"], "coarse_3"),
            "gold_entities": base["gold_entities"],
            "gold_status": base["gold_operative_status"],
            "gold_relation": base["gold_relation"],
            "gold_answer": base["gold_answer_relevant"],
        }
        for variant, row in pred_rows.items():
            score = scores[variant]
            out.update({
                f"{variant}_role": row["pred_role"],
                f"{variant}_role_correct": yn(score["role"]),
                f"{variant}_coarse_5_correct": yn(score["coarse_5"]),
                f"{variant}_coarse_4_correct": yn(score["coarse_4"]),
                f"{variant}_coarse_3_correct": yn(score["coarse_3"]),
                f"{variant}_entities": row["pred_entities"],
                f"{variant}_entity_jaccard": f"{score['entity_jaccard']:.6f}",
                f"{variant}_entity_exact": yn(score["entity_exact"]),
                f"{variant}_status": row["pred_operative_status"],
                f"{variant}_status_correct": yn(score["status"]),
                f"{variant}_relation": row["pred_relation"],
                f"{variant}_relation_correct": yn(score["relation"]),
                f"{variant}_answer": row["pred_answer_relevant"],
                f"{variant}_answer_correct": yn(score["answer"]),
                f"{variant}_strict_correct": yn(score["strict"]),
                f"{variant}_relaxed_1_correct": yn(score["relaxed_1"]),
                f"{variant}_relaxed_2_correct": yn(score["relaxed_2"]),
                f"{variant}_relaxed_3_correct": yn(score["relaxed_3"]),
            })
        blockers = strict_blockers(scores["R6"])
        out["R6_strict_blockers"] = "; ".join(blockers) if blockers else "none"
        out["outcome_bucket"] = classify(scores, pred_rows)
        audit_rows.append(out)
    return audit_rows


def summarize(rows):
    metrics = {}
    for variant in ["combined_v3", "D", "R6"]:
        metrics[variant] = {}
        for metric in METRICS:
            if metric == "entity_jaccard":
                metrics[variant][metric] = safe_div(sum(row["_scores"][variant][metric] for row in rows), len(rows))
            else:
                metrics[variant][metric] = safe_div(sum(int(row["_scores"][variant][metric]) for row in rows), len(rows))
    return metrics


def blocker_counts(rows):
    counts = Counter()
    for row in rows:
        for blocker in row["R6_strict_blockers"].split("; "):
            if blocker and blocker != "none":
                counts[blocker] += 1
    return counts


def role_counts(rows):
    counts = Counter()
    for row in rows:
        d_score = row["_scores"]["D"]
        r6 = row["_scores"]["R6"]
        if row["D_role"] != row["R6_role"]:
            counts["coarse_3_guard_changed_D_role"] += 1
            if score_total(r6) > score_total(d_score):
                counts["changes_helped"] += 1
            elif score_total(r6) < score_total(d_score):
                counts["changes_hurt"] += 1
        if r6["role"] and not r6["strict"]:
            counts["R6_fine_role_correct_but_strict_fails"] += 1
    return counts


def audit_answers(metrics, blockers):
    combined = metrics["combined_v3"]
    r6 = metrics["R6"]
    overfit_evidence = r6["role"] <= combined["role"] and r6["relaxed_1"] <= combined["relaxed_1"] and r6["strict"] < combined["strict"]
    return {
        "A_role": r6["role"] > combined["role"],
        "B_coarse3": r6["coarse_3"] >= combined["coarse_3"],
        "C_relaxed1": r6["relaxed_1"] > combined["relaxed_1"],
        "D_relaxed2": r6["relaxed_2"] >= combined["relaxed_2"],
        "E_relaxed3": r6["relaxed_3"] >= combined["relaxed_3"],
        "F_loses_strict": r6["strict"] < combined["strict"],
        "G_entity_main": blockers["entity"] >= max(blockers["relation"], blockers["status"], blockers["role"], blockers["answer"]),
        "H_relation_secondary": blockers["relation"] >= max(blockers["status"], blockers["role"], blockers["answer"]),
        "I_overfit_evidence": overfit_evidence,
    }


def final_verdict(answers):
    if all(answers[key] for key in ["A_role", "B_coarse3", "C_relaxed1", "D_relaxed2", "E_relaxed3"]) and not answers["F_loses_strict"]:
        return "promote R6 as RouteMap v2 default candidate"
    if answers["I_overfit_evidence"]:
        return "reject R6 as unstable or overfit"
    return "keep R6 provisional pending more true-blind rows"


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def write_outputs(rows, metrics, blockers, buckets, roles, answers, verdict):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in AUDIT_FIELDS})

    metric_rows = []
    for variant in ["combined_v3", "D", "R6"]:
        metric_rows.append([variant, *[pct(metrics[variant][metric]) for metric in METRICS]])

    lines = ["# True-Blind R6 Candidate Audit", "", "## Audit Answers", ""]
    lines.extend(md_table(["question", "answer"], [
        ["A. Does R6 beat combined_v3 on role?", yn(answers["A_role"])],
        ["B. Does R6 preserve combined_v3 coarse_3?", yn(answers["B_coarse3"])],
        ["C. Does R6 beat combined_v3 on relaxed_1?", yn(answers["C_relaxed1"])],
        ["D. Does R6 match or beat combined_v3 on relaxed_2?", yn(answers["D_relaxed2"])],
        ["E. Does R6 match combined_v3 on relaxed_3?", yn(answers["E_relaxed3"])],
        ["F. Does R6 lose strict accuracy?", yn(answers["F_loses_strict"])],
        ["G. Is entity exact still the main strict blocker?", yn(answers["G_entity_main"])],
        ["H. Is relation still secondary?", yn(answers["H_relation_secondary"])],
        ["I. Is there evidence R6 overfit earlier splits?", yn(answers["I_overfit_evidence"])],
        ["J. Should R6 be promoted as RouteMap v2 default candidate?", yn(verdict == "promote R6 as RouteMap v2 default candidate")],
    ]))
    lines.extend(["", "## Metrics", ""])
    lines.extend(md_table(["variant", *METRICS], metric_rows))
    lines.extend(["", "## R6 Strict Blockers", ""])
    lines.extend(md_table(["blocker", "rows"], [[key, blockers[key]] for key in ["entity", "relation", "status", "role", "answer", "multiple"]]))
    lines.extend(["", "## Outcome Buckets", ""])
    lines.extend(md_table(["outcome_bucket", "rows"], buckets.most_common()))
    lines.extend(["", "## Role Guard Counts", ""])
    lines.extend(md_table(["measure", "rows"], roles.most_common()))
    lines.extend(["", "## Final Verdict", "", verdict])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "rows": len(rows),
        "metrics": metrics,
        "R6_strict_blocker_counts": dict(blockers),
        "row_bucket_counts": dict(buckets),
        "role_guard_counts": dict(roles),
        "audit_answers": answers,
        "final_verdict": verdict,
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    rows = build_rows()
    metrics = summarize(rows)
    blockers = blocker_counts(rows)
    buckets = Counter(row["outcome_bucket"] for row in rows)
    roles = role_counts(rows)
    answers = audit_answers(metrics, blockers)
    verdict = final_verdict(answers)
    write_outputs(rows, metrics, blockers, buckets, roles, answers, verdict)
    print("true_blind_r6_audit")
    print(f"row_count={len(rows)}")
    for variant in ["combined_v3", "D", "R6"]:
        print(f"{variant}: " + " ".join(f"{metric}={metrics[variant][metric]:.3f}" for metric in METRICS))
    print("R6_blocker_counts")
    for key, count in blockers.most_common():
        print(f"{key}: {count}")
    print(f"final_verdict={verdict}")
    print(f"audit_csv={OUT_CSV.relative_to(ROOT)}")
    print(f"audit_md={OUT_MD.relative_to(ROOT)}")
    print(f"audit_json={OUT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
