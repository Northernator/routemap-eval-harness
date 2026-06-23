import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import build_heldout_r6_predictions as r6_builder
from compare_heldout_r6_results import METRICS, evaluate, fmt
from validate_true_blind_gold import GOLD, validate


ROOT = Path(__file__).resolve().parents[1]
TRUE_BLIND_ROOT = ROOT / "data/v1/true_blind_natural_language"
RAW_DOCS = TRUE_BLIND_ROOT / "raw_docs"
ANNOTATION_DIR = TRUE_BLIND_ROOT / "annotation"
PRED_DIR = TRUE_BLIND_ROOT / "predictions"
REPORT_DIR = TRUE_BLIND_ROOT / "reports"

FROZEN_GOLD = ANNOTATION_DIR / "true_blind_gold_frozen.csv"
FREEZE_MANIFEST = REPORT_DIR / "TRUE_BLIND_GOLD_FREEZE.json"
EVALUATOR = ROOT / "src/evaluate_llm_extraction_predictions.py"

PREDICTIONS = {
    "combined_v3": PRED_DIR / "combined_v3_true_blind_predictions.csv",
    "D_add_combined_answer": PRED_DIR / "D_true_blind_predictions.csv",
    "R6": PRED_DIR / "R6_true_blind_predictions.csv",
}

EVAL_REPORTS = {
    "combined_v3": REPORT_DIR / "combined_v3_true_blind_evaluation.md",
    "D_add_combined_answer": REPORT_DIR / "D_true_blind_evaluation.md",
    "R6": REPORT_DIR / "R6_true_blind_evaluation.md",
}

COMPARISON_MD = REPORT_DIR / "TRUE_BLIND_R6_COMPARISON.md"
COMPARISON_CSV = REPORT_DIR / "true_blind_r6_comparison.csv"


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def raw_doc_count():
    return len(sorted(RAW_DOCS.glob("*.md")) + sorted(RAW_DOCS.glob("*.txt")))


def freeze_gold(rows):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    current_hash = file_sha256(GOLD)
    manifest = {
        "gold_path": str(GOLD.relative_to(ROOT)),
        "frozen_gold_path": str(FROZEN_GOLD.relative_to(ROOT)),
        "sha256": current_hash,
        "rows": len(rows),
        "rule": "Gold frozen before predictions; do not tune combined_v3, D, R6, prompts, taxonomies, mappings, thresholds, or evaluator logic from this test.",
    }
    if FREEZE_MANIFEST.exists():
        previous = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
        if previous.get("sha256") != current_hash:
            raise ValueError(
                "true_blind_gold.csv changed after freeze. Refusing to evaluate; create a new named benchmark if labels changed."
            )
    else:
        shutil.copyfile(GOLD, FROZEN_GOLD)
        FREEZE_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not FROZEN_GOLD.exists():
        shutil.copyfile(GOLD, FROZEN_GOLD)
    return manifest


def configure_builder():
    r6_builder.SOURCE_SPLIT = FROZEN_GOLD
    r6_builder.OUT_ROOT = TRUE_BLIND_ROOT
    r6_builder.PRED_DIR = PRED_DIR
    r6_builder.REPORT_DIR = REPORT_DIR
    r6_builder.RAW_OLLAMA_OUT = PRED_DIR / "ollama_llama31_true_blind_outputs.jsonl"
    r6_builder.COMBINED_OUT = PREDICTIONS["combined_v3"]
    r6_builder.D_OUT = PREDICTIONS["D_add_combined_answer"]
    r6_builder.R6_OUT = PREDICTIONS["R6"]
    r6_builder.PROVENANCE_OUT = REPORT_DIR / "TRUE_BLIND_R6_PREDICTION_PROVENANCE.md"


def run_existing_evaluator():
    for variant, pred_path in PREDICTIONS.items():
        out_rows = REPORT_DIR / f"{variant}_true_blind_evaluation_rows.csv"
        subprocess.run(
            [
                sys.executable,
                str(EVALUATOR),
                "--csv",
                str(pred_path),
                "--out-md",
                str(EVAL_REPORTS[variant]),
                "--out-csv",
                str(out_rows),
            ],
            cwd=str(ROOT),
            check=True,
        )


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def collect_comparison():
    return [{"variant": name, **evaluate(read_rows(path))} for name, path in PREDICTIONS.items()]


def final_verdict(rows):
    by_name = {row["variant"]: row for row in rows}
    combined = by_name["combined_v3"]
    r6 = by_name["R6"]
    checks = {
        "role_beats_combined": r6["role"] > combined["role"],
        "coarse_3_preserved_or_improved": r6["coarse_3"] >= combined["coarse_3"],
        "relaxed_1_beats_combined": r6["relaxed_1"] > combined["relaxed_1"],
        "relaxed_2_matches_or_beats_combined": r6["relaxed_2"] >= combined["relaxed_2"],
        "relaxed_3_matches_combined": r6["relaxed_3"] >= combined["relaxed_3"],
        "strict_not_lower_than_combined": r6["strict"] >= combined["strict"],
    }
    if all(checks.values()):
        return "promote R6 as RouteMap v2 default candidate", checks
    if r6["role"] <= combined["role"] and r6["relaxed_1"] <= combined["relaxed_1"] and r6["strict"] < combined["strict"]:
        return "reject R6 as unstable or overfit", checks
    return "keep R6 provisional pending more true-blind rows", checks


def write_comparison(rows, verdict, checks):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with COMPARISON_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["variant", *METRICS])
        writer.writeheader()
        writer.writerows(rows)

    headers = ["variant", *METRICS]
    lines = [
        "# True-Blind R6 Comparison",
        "",
        "Gold labels were frozen before predictions. This report must not be used to tune combined_v3, D, R6, prompts, taxonomies, mappings, thresholds, or evaluator logic.",
        "",
        "## Metrics",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join([row["variant"], *[fmt(row[metric]) for metric in METRICS]]) + " |")
    lines.extend(["", "## R6 Checks", "", "| check | passed |", "|---|---:|"])
    for key, passed in checks.items():
        lines.append(f"| {key} | {'YES' if passed else 'NO'} |")
    lines.extend(["", "## Final Verdict", "", verdict])
    COMPARISON_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_table(rows, verdict):
    print("final_metrics_table")
    print(",".join(["variant", *METRICS]))
    for row in rows:
        print(",".join([row["variant"], *[fmt(row[metric]) for metric in METRICS]]))
    print(f"row_count={rows[0]['evaluated_rows'] if rows else 0}")
    print(f"final_verdict={verdict}")


def main():
    print(f"raw_docs_found={raw_doc_count()}")
    print("annotation_batch_path=data/v1/true_blind_natural_language/annotation/true_blind_annotation_batch.csv")
    if not GOLD.exists():
        print("gold_validation_result=not_run_missing_human_gold")
        print("evaluation_ran=NO")
        print("Add new blind raw docs, then rerun this script.")
        return
    rows = validate(GOLD)
    manifest = freeze_gold(rows)
    print(f"gold_freeze_sha256={manifest['sha256']}")
    configure_builder()
    r6_builder.main()
    run_existing_evaluator()
    comparison = collect_comparison()
    verdict, checks = final_verdict(comparison)
    write_comparison(comparison, verdict, checks)
    print("evaluation_ran=YES")
    print_table(comparison, verdict)
    print(f"comparison_report={COMPARISON_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
