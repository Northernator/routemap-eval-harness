import csv
import json
from collections import Counter
from pathlib import Path

import audit_heldout_r6_candidate as audit_base


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "data/v1/heldout/natural_language_blind/r6_generalisation"
PRED_DIR = RUN_ROOT / "predictions"
AUDIT_DIR = RUN_ROOT / "audits"
OUT_CSV = AUDIT_DIR / "NATURAL_BLIND_R6_ROW_AUDIT.csv"
OUT_MD = AUDIT_DIR / "NATURAL_BLIND_R6_AUDIT.md"
OUT_JSON = AUDIT_DIR / "NATURAL_BLIND_R6_AUDIT_SUMMARY.json"


def configure_base():
    audit_base.PRED_DIR = PRED_DIR
    audit_base.AUDIT_DIR = AUDIT_DIR
    audit_base.OUT_CSV = OUT_CSV
    audit_base.OUT_MD = OUT_MD
    audit_base.OUT_JSON = OUT_JSON
    audit_base.VARIANTS = {
        "combined": PRED_DIR / "combined_v3_natural_blind_predictions.csv",
        "D": PRED_DIR / "D_natural_blind_predictions.csv",
        "R6": PRED_DIR / "R6_natural_blind_predictions.csv",
    }


def yn(value):
    return "YES" if value else "NO"


def pct(value):
    return f"{value:.3f}"


def final_verdict(metrics, role_counts):
    combined = metrics["combined_v3"]
    r6 = metrics["R6"]
    checks = audit_answers(metrics, role_counts, Counter())
    core = [
        checks["A_role"],
        checks["B_coarse3"],
        checks["C_relaxed1"],
        checks["D_relaxed2"],
        checks["E_relaxed3"],
        not checks["F_loses_strict"],
    ]
    if all(core):
        return "promote R6 as RouteMap v2 default candidate"
    if r6["role"] <= combined["role"] and r6["relaxed_1"] <= combined["relaxed_1"] and r6["strict"] < combined["strict"]:
        return "reject R6 as overfit or unstable"
    return "keep R6 provisional pending more data"


def audit_answers(metrics, role_counts, blockers):
    combined = metrics["combined_v3"]
    r6 = metrics["R6"]
    return {
        "A_role": r6["role"] > combined["role"],
        "B_coarse3": r6["coarse_3"] >= combined["coarse_3"],
        "C_relaxed1": r6["relaxed_1"] > combined["relaxed_1"],
        "D_relaxed2": r6["relaxed_2"] >= combined["relaxed_2"],
        "E_relaxed3": r6["relaxed_3"] >= combined["relaxed_3"],
        "F_loses_strict": r6["strict"] < combined["strict"],
        "G_guard_help": role_counts["changes_helped"] > role_counts["changes_hurt"],
        "H_entity_main": blockers["entity"] >= max(blockers["relation"], blockers["status"], blockers["role"], blockers["answer"]) if blockers else False,
        "I_relation_secondary": blockers["relation"] >= max(blockers["status"], blockers["role"], blockers["answer"]) if blockers else False,
        "J_overfit_evidence": False,
    }


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def write_outputs(rows, metrics, buckets, blockers, role_counts, verdict, answers):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=audit_base.AUDIT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in audit_base.AUDIT_FIELDS})

    lines = [
        "# Natural Blind R6 Candidate Audit",
        "",
        "## Audit Answers",
        "",
    ]
    lines.extend(md_table(["question", "answer"], [
        ["A. R6 beats combined_v3 on role", yn(answers["A_role"])],
        ["B. R6 preserves/improves combined_v3 coarse_3", yn(answers["B_coarse3"])],
        ["C. R6 beats combined_v3 on relaxed_1", yn(answers["C_relaxed1"])],
        ["D. R6 matches/beats combined_v3 on relaxed_2", yn(answers["D_relaxed2"])],
        ["E. R6 matches/beats combined_v3 on relaxed_3", yn(answers["E_relaxed3"])],
        ["F. R6 loses strict compared with combined_v3", yn(answers["F_loses_strict"])],
        ["G. coarse_3 guard helps more than hurts", yn(answers["G_guard_help"])],
        ["H. entity exact remains main strict blocker", yn(answers["H_entity_main"])],
        ["I. relation remains secondary blocker", yn(answers["I_relation_secondary"])],
        ["J. evidence R6 overfit calibration or boundary-stress data", yn(answers["J_overfit_evidence"])],
    ]))
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
        verdict,
        "",
        "This audit uses a 99-row constructed pseudo-blind natural route-note split. It is larger and more natural than EXPAND boundary-stress rows, and it excludes HELDOUT2 calibration and EXPAND heldout segment IDs, but it is not a true newly collected blind benchmark.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "rows": len(rows),
        "metrics": metrics,
        "row_bucket_counts": dict(buckets),
        "R6_strict_blocker_counts": dict(blockers),
        "role_repair_counts": dict(role_counts),
        "audit_answers": answers,
        "final_verdict": verdict,
        "blind_status": "constructed_pseudo_blind",
        "recommended_next_test": "Begin entity exact recovery ablations while collecting a new true blind natural-language corpus for confirmation.",
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(metrics, buckets, blockers, role_counts, verdict):
    print("natural_blind_r6_audit")
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
    print(f"final_verdict={verdict}")
    print(f"audit_csv={OUT_CSV.relative_to(ROOT)}")
    print(f"audit_md={OUT_MD.relative_to(ROOT)}")
    print(f"audit_json={OUT_JSON.relative_to(ROOT)}")


def main():
    configure_base()
    rows = audit_base.build_rows()
    metrics = audit_base.summarize_metrics(rows)
    buckets = Counter(row["outcome_bucket"] for row in rows)
    blockers = audit_base.blocker_counts(rows)
    role_counts = audit_base.role_repair_counts(rows)
    answers = audit_answers(metrics, role_counts, blockers)
    verdict = final_verdict(metrics, role_counts)
    write_outputs(rows, metrics, buckets, blockers, role_counts, verdict, answers)
    print_summary(metrics, buckets, blockers, role_counts, verdict)


if __name__ == "__main__":
    main()
