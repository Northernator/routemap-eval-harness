import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

from build_true_blind_entity_alias_map_v1 import (
    APPLIED_OUT,
    REVIEW_OUT,
    main as build_alias_map,
    parse_entities,
)
from entity_ontology_v1 import format_entity_set as format_v1
from entity_ontology_v1 import normalize_entity as normalize_v1
from entity_ontology_v1_plus_true_blind import format_entity_set as format_v1_plus
from entity_ontology_v1_plus_true_blind import normalize_entity as normalize_v1_plus


ROOT = Path(__file__).resolve().parents[1]
ABLATION_ROOT = ROOT / "data/v1/true_blind_natural_language/ablations/entity_ontology_alignment_v1"
PRED_ALIGNED = ABLATION_ROOT / "predictions_aligned"
REPORT_DIR = ABLATION_ROOT / "reports"
COMPARISON_MD = ABLATION_ROOT / "ENTITY_ALIGNMENT_ABLATION_V1_COMPARISON.md"
SUMMARY_JSON = ABLATION_ROOT / "ENTITY_ALIGNMENT_ABLATION_V1_SUMMARY.json"
EVAL_SCRIPT = ROOT / "src/evaluate_entity_alignment_ablation.py"

ORIGINALS = {
    "combined_v3": ROOT / "data/v1/true_blind_natural_language/predictions/combined_v3_true_blind_predictions.csv",
    "D": ROOT / "data/v1/true_blind_natural_language/predictions/D_true_blind_predictions.csv",
    "R6": ROOT / "data/v1/true_blind_natural_language/predictions/R6_true_blind_predictions.csv",
}
METRICS = [
    "evaluated_rows",
    "missing_invalid_rows",
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


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_alias_map():
    if not APPLIED_OUT.exists():
        build_alias_map()
    return {row["gold_entity"]: row["mapped_canonical"] for row in read_csv(APPLIED_OUT)}


def alias_coverage():
    review_rows = read_csv(REVIEW_OUT)
    applied = read_csv(APPLIED_OUT)
    unique = len(review_rows)
    mapped_high_medium = sum(1 for row in review_rows if row["confidence"] in {"high", "medium"} and row["approved"] == "yes" and row["mapped_canonical"])
    mapped_low_approved = sum(1 for row in review_rows if row["confidence"] == "low" and row["approved"] == "yes" and row["mapped_canonical"])
    total = len(applied)
    return {
        "unique_gold_entities": unique,
        "mapped_high_medium": mapped_high_medium,
        "mapped_low_approved": mapped_low_approved,
        "total_applied": total,
        "coverage_fraction": total / unique if unique else 0.0,
    }


def delimiter_only_entities(raw):
    return "; ".join(parse_entities(raw))


def option_a_entities(raw, alias_map):
    values = []
    for entity in parse_entities(raw):
        key = entity.lower().strip()
        mapped = alias_map.get(key)
        values.append(mapped if mapped else key)
    return format_v1(set(values))


def option_b_entities(raw, alias_map):
    values = []
    for entity in parse_entities(raw):
        key = entity.lower().strip()
        mapped = alias_map.get(key)
        values.append(mapped if mapped else key)
    return format_v1_plus({normalize_v1_plus(value) for value in values if value})


def build_condition_copy(condition, variant, source, alias_map):
    rows = read_csv(source)
    out_rows = []
    for row in rows:
        out = dict(row)
        if condition == "C1_delimiter_only":
            out["gold_entities"] = delimiter_only_entities(row.get("gold_entities", ""))
        elif condition == "C2_option_a_alias":
            out["gold_entities"] = option_a_entities(row.get("gold_entities", ""), alias_map)
        elif condition in {"C3_option_b_expanded", "C3_option_b_expanded_PROPOSAL"}:
            out["gold_entities"] = option_b_entities(row.get("gold_entities", ""), alias_map)
            out["pred_entities"] = format_v1_plus({normalize_v1_plus(value) for value in parse_entities(row.get("pred_entities", "")) if value})
        else:
            raise ValueError(f"Unknown copy condition: {condition}")
        out_rows.append(out)
    out_path = PRED_ALIGNED / condition / f"{variant}_true_blind_predictions_{condition}.csv"
    write_csv(out_path, out_rows, list(rows[0].keys()))
    return out_path


def run_eval(condition, variant, csv_path, ontology):
    md = REPORT_DIR / condition / f"{variant}_{condition}_{ontology}.md"
    rows_csv = REPORT_DIR / condition / f"{variant}_{condition}_{ontology}_rows.csv"
    cmd = [
        sys.executable,
        str(EVAL_SCRIPT),
        "--csv",
        str(csv_path),
        "--ontology",
        ontology,
        "--out-md",
        str(md),
        "--out-csv",
        str(rows_csv),
    ]
    output = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, check=True)
    metrics = {}
    for line in output.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in METRICS:
            metrics[key] = int(value) if key in {"evaluated_rows", "missing_invalid_rows"} else float(value)
    missing = [metric for metric in METRICS if metric not in metrics]
    if missing:
        raise ValueError(f"Missing metrics from evaluator for {condition}/{variant}: {missing}")
    return metrics


def parity_check(metrics):
    combined = metrics["C0_original"]["combined_v3"]
    checks = {
        "role": abs(combined["role"] - 0.3055555555555556) < 0.001,
        "entity_jaccard": combined["entity_jaccard"] == 0.0,
        "coarse_3": abs(combined["coarse_3"] - 0.5555555555555556) < 0.001,
    }
    if not all(checks.values()):
        raise SystemExit(f"C0 parity check failed: {checks}; combined_v3={combined}")
    return checks


def r6_checks(condition_metrics):
    combined = condition_metrics["combined_v3"]
    r6 = condition_metrics["R6"]
    return {
        "role_beats_combined": r6["role"] > combined["role"],
        "coarse_3_preserved_or_improved": r6["coarse_3"] >= combined["coarse_3"],
        "relaxed_1_beats_combined": r6["relaxed_1"] > combined["relaxed_1"],
        "relaxed_2_matches_or_beats_combined": r6["relaxed_2"] >= combined["relaxed_2"],
        "relaxed_3_matches_combined": r6["relaxed_3"] >= combined["relaxed_3"],
        "strict_not_lower_than_combined": r6["strict"] >= combined["strict"],
    }


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def recommendation(flags):
    if flags["alias_alignment_reaches_target_band"]:
        return "Alias-aligned ontology_v1 copy recovers entity Jaccard into target band; use C2 as a named ablation for fair model-quality reading, without changing locked true-blind results."
    if flags["ontology_expansion_attempted"] and flags.get("ontology_expansion_helps"):
        return "Ontology expansion materially helps; next step is human-reviewed domain ontology design or domain-general entity matching, reported as a separate ablation."
    return "Delimiter and high/medium alias map are insufficient; run human-reviewed ontology expansion or domain-general entity matching before interpreting entity-dependent strict/relaxed metrics."


def write_outputs(metrics, coverage, flags, c2_checks, c3_checks, recommendation_text):
    rows = []
    for condition, variants in metrics.items():
        for variant, row in variants.items():
            rows.append([
                condition,
                variant,
                f"{row['role']:.3f}",
                f"{row['coarse_3']:.3f}",
                f"{row['entity_jaccard']:.3f}",
                f"{row['entity_exact']:.3f}",
                f"{row['strict']:.3f}",
                f"{row['relaxed_1']:.3f}",
                f"{row['relaxed_2']:.3f}",
                f"{row['relaxed_3']:.3f}",
            ])
    lines = [
        "# Entity Alignment Ablation v1 Comparison",
        "",
        "ABLATION ONLY. Gold was frozen before prediction. These results must not promote R6 or tune the locked true-blind test, prompts, taxonomies, thresholds, ontology, or evaluator.",
        "",
        "## Metrics",
        "",
    ]
    lines.extend(md_table(["condition", "variant", "role", "coarse_3", "entity_jaccard", "entity_exact", "strict", "relaxed_1", "relaxed_2", "relaxed_3"], rows))
    lines.extend(["", "## Alias Coverage", ""])
    lines.extend(md_table(["measure", "value"], [[key, f"{value:.6f}" if isinstance(value, float) else value] for key, value in coverage.items()]))
    lines.extend(["", "## Verdict Checks", ""])
    lines.extend(md_table(["check", "value"], [[key, "YES" if value else "NO"] for key, value in flags.items()]))
    lines.extend(["", "## ABLATION Fair R6 Read", "", "C2 checks:", ""])
    lines.extend(md_table(["check", "value"], [[key, "YES" if value else "NO"] for key, value in c2_checks.items()]))
    if c3_checks:
        lines.extend(["", "C3 PROPOSAL checks:", ""])
        lines.extend(md_table(["check", "value"], [[key, "YES" if value else "NO"] for key, value in c3_checks.items()]))
    lines.extend(["", "## Recommendation", "", recommendation_text])
    COMPARISON_MD.parent.mkdir(parents=True, exist_ok=True)
    COMPARISON_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = {
        "ablation": "true_blind_entity_ontology_alignment_v1",
        "metrics": metrics,
        "alias_coverage": coverage,
        "condition_flags": flags,
        "fair_r6_read_C2": c2_checks,
        "fair_r6_read_C3": c3_checks,
        "recommendation": recommendation_text,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_table(metrics):
    print("ENTITY_ALIGNMENT_ABLATION_V1_FINAL_TABLE")
    print("condition,variant,role,coarse_3,entity_jaccard,entity_exact,strict,relaxed_1,relaxed_2,relaxed_3")
    for condition, variants in metrics.items():
        for variant, row in variants.items():
            print(",".join([
                condition,
                variant,
                f"{row['role']:.6f}",
                f"{row['coarse_3']:.6f}",
                f"{row['entity_jaccard']:.6f}",
                f"{row['entity_exact']:.6f}",
                f"{row['strict']:.6f}",
                f"{row['relaxed_1']:.6f}",
                f"{row['relaxed_2']:.6f}",
                f"{row['relaxed_3']:.6f}",
            ]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-option-b", action="store_true")
    parser.add_argument("--coverage-threshold", type=float, default=0.40)
    parser.add_argument("--jaccard-target", type=float, default=0.23)
    args = parser.parse_args()

    build_alias_map()
    alias_map = load_alias_map()
    coverage = alias_coverage()
    metrics = {"C0_original": {}, "C1_delimiter_only": {}, "C2_option_a_alias": {}}

    for variant, path in ORIGINALS.items():
        metrics["C0_original"][variant] = run_eval("C0_original", variant, path, "v1")
    parity = parity_check(metrics)

    for condition in ["C1_delimiter_only", "C2_option_a_alias"]:
        for variant, source in ORIGINALS.items():
            copy_path = build_condition_copy(condition, variant, source, alias_map)
            metrics[condition][variant] = run_eval(condition, variant, copy_path, "v1")

    c2_combined = metrics["C2_option_a_alias"]["combined_v3"]
    run_c3 = args.run_option_b or (
        coverage["coverage_fraction"] < args.coverage_threshold
        and c2_combined["entity_jaccard"] < args.jaccard_target
    )
    if run_c3:
        metrics["C3_option_b_expanded_PROPOSAL"] = {}
        for variant, source in ORIGINALS.items():
            copy_path = build_condition_copy("C3_option_b_expanded_PROPOSAL", variant, source, alias_map)
            metrics["C3_option_b_expanded_PROPOSAL"][variant] = run_eval("C3_option_b_expanded_PROPOSAL", variant, copy_path, "v1_plus")

    flags = {
        "parity_check_passed": all(parity.values()),
        "delimiter_fix_recovers_jaccard": metrics["C1_delimiter_only"]["combined_v3"]["entity_jaccard"] > 0,
        "alias_alignment_reaches_target_band": c2_combined["entity_jaccard"] >= args.jaccard_target,
        "ontology_expansion_attempted": run_c3,
    }
    if run_c3:
        flags["ontology_expansion_helps"] = (
            metrics["C3_option_b_expanded_PROPOSAL"]["combined_v3"]["entity_jaccard"]
            > metrics["C2_option_a_alias"]["combined_v3"]["entity_jaccard"]
        )
    c2_checks = r6_checks(metrics["C2_option_a_alias"])
    c3_checks = r6_checks(metrics["C3_option_b_expanded_PROPOSAL"]) if run_c3 else {}
    recommendation_text = recommendation(flags)
    write_outputs(metrics, coverage, flags, c2_checks, c3_checks, recommendation_text)
    print_table(metrics)
    print("alias_coverage=" + json.dumps(coverage, sort_keys=True))
    print("condition_flags=" + json.dumps(flags, sort_keys=True))
    print("recommendation=" + recommendation_text)
    print(f"comparison_md={COMPARISON_MD.relative_to(ROOT)}")
    print(f"summary_json={SUMMARY_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
