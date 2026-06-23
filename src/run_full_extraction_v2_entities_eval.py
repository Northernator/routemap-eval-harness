"""Run full_extraction_with_v2_entities experiment."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import build_full_extraction_pred_with_v2_entities as builder
import evaluate_full_extraction_custom_cols as exact_eval
import evaluate_full_extraction_soft_entities as soft_eval


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/v1/full_extraction_experiments/v2_entities"
PRED_DIR = OUT_DIR / "predictions"
REPORT_DIR = OUT_DIR / "reports"
MISMATCH_DIR = OUT_DIR / "mismatches"
REPORT_PATH = OUT_DIR / "FULL_EXTRACTION_V2_ENTITIES_REPORT.md"
SUMMARY_PATH = OUT_DIR / "SUMMARY.json"

DATASETS = {
    "in_domain_dev": PRED_DIR / "in_domain_dev__with_v2_entities.csv",
    "true_blind_combined_v3": PRED_DIR / "true_blind_combined_v3__with_v2_entities.csv",
    "true_blind_R6": PRED_DIR / "true_blind_R6__with_v2_entities.csv",
}

VARIANTS = {
    "V0_pred_entities": {
        "entities_col": "pred_entities",
        "role_col": "pred_role",
        "status_col": "pred_operative_status",
        "relation_col": "pred_relation",
        "answer_col": "pred_answer_relevant",
    },
    "V_ontology": {
        "entities_col": "pred_entities_ontology",
        "role_col": "pred_role",
        "status_col": "pred_operative_status",
        "relation_col": "pred_relation",
        "answer_col": "pred_answer_relevant",
    },
    "V2": {
        "entities_col": "pred_entities_v2",
        "role_col": "pred_role",
        "status_col": "pred_operative_status",
        "relation_col": "pred_relation",
        "answer_col": "pred_answer_relevant",
    },
    "DIAGNOSTIC_gold_other_V2": {
        "entities_col": "pred_entities_v2",
        "role_col": "pred_role_goldother",
        "status_col": "pred_operative_status_goldother",
        "relation_col": "pred_relation_goldother",
        "answer_col": "pred_answer_relevant_goldother",
    },
}


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def eval_rows(path):
    rows = read_rows(path)
    return rows, [row for row in rows if row.get("include_in_eval", "YES") in {"", "YES"}]


def write_exact_report(path, total_rows, excluded_rows, metrics):
    exact_eval.write_markdown(path, total_rows, excluded_rows, metrics)


def run_exact(dataset, variant, csv_path, spec):
    all_rows, rows = eval_rows(csv_path)
    metrics = exact_eval.evaluate(
        rows,
        spec["role_col"],
        spec["entities_col"],
        spec["status_col"],
        spec["relation_col"],
        spec["answer_col"],
    )
    mismatch_path = MISMATCH_DIR / f"{dataset}__{variant}__exact_mismatches.csv"
    report_path = REPORT_DIR / f"{dataset}__{variant}__exact.md"
    exact_eval.write_mismatches(mismatch_path, metrics["mismatch_rows"])
    write_exact_report(report_path, len(all_rows), len(all_rows) - len(rows), metrics)
    return metrics, mismatch_path, report_path


def run_soft(dataset, variant, csv_path, spec, matcher):
    all_rows, rows = eval_rows(csv_path)
    metrics = soft_eval.evaluate(
        rows,
        spec["role_col"],
        spec["entities_col"],
        spec["status_col"],
        spec["relation_col"],
        spec["answer_col"],
        matcher,
    )
    mismatch_path = MISMATCH_DIR / f"{dataset}__{variant}__soft_{matcher}_mismatches.csv"
    report_path = REPORT_DIR / f"{dataset}__{variant}__soft_{matcher}.md"
    soft_eval.write_mismatches(mismatch_path, metrics["mismatch_rows"])
    soft_eval.write_markdown(report_path, len(all_rows), len(all_rows) - len(rows), metrics)
    return metrics, mismatch_path, report_path


def metric_row(dataset, variant, mode, metrics):
    return {
        "dataset": dataset,
        "variant": variant,
        "metric_mode": mode,
        "evaluated_rows": metrics.get("evaluated_rows", 0),
        "role_accuracy": metrics.get("role_accuracy", 0.0),
        "entity_avg_jaccard": metrics.get("entity_average_softjaccard", metrics.get("entity_average_jaccard", 0.0)),
        "entity_avg_precision": metrics.get("entity_average_precision", 0.0),
        "entity_avg_recall": metrics.get("entity_average_recall", 0.0),
        "entity_avg_f1": metrics.get("entity_average_f1", 0.0),
        "strict": metrics.get("strict_full_row_accuracy", 0.0),
        "relaxed_1": metrics.get("relaxed_1", 0.0),
        "relaxed_2": metrics.get("relaxed_2", 0.0),
        "relaxed_3": metrics.get("relaxed_3", 0.0),
    }


def fmt(value):
    if isinstance(value, (float, int)):
        return f"{value:.6f}"
    return str(value)


def markdown_table(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def role_accuracy_flags(rows):
    flags = {}
    for dataset in DATASETS:
        non_diag = [row for row in rows if row["dataset"] == dataset and row["variant"] != "DIAGNOSTIC_gold_other_V2"]
        values = {round(row["role_accuracy"], 12) for row in non_diag}
        flags[dataset] = len(values) <= 1
    return flags


def approx_zero(value):
    return abs(value) <= 0.005


def write_report(summary):
    columns = [
        "variant",
        "metric_mode",
        "entity_avg_jaccard",
        "strict",
        "relaxed_1",
        "relaxed_2",
        "relaxed_3",
        "role_accuracy",
    ]
    lines = [
        "# full_extraction_with_v2_entities",
        "",
        "Development read. V2 entities are frozen via extract_entities_hybrid_v2 module constants. Allowed dev and frozen true-blind prediction copies only; locked fresh/adjudicated test files were not read or modified.",
        "",
        "Prior context: strict full-row was 0.000 on true-blind exact scoring; ontology_v1 in-domain entity Jaccard context was 0.506.",
    ]
    for dataset in DATASETS:
        rows = [row for row in summary["table_rows"] if row["dataset"] == dataset]
        lines.extend(["", f"## {dataset}", "", markdown_table(rows, columns)])
    lines.extend(
        [
            "",
            "## Role Accuracy Constant Check",
            "",
            markdown_table(
                [{"dataset": key, "role_accuracy_constant": value} for key, value in summary["role_accuracy_constant"].items()],
                ["dataset", "role_accuracy_constant"],
            ),
            "",
            "## Verdicts",
            "",
            markdown_table([summary["verdicts"]], list(summary["verdicts"].keys())),
            "",
            "## Recommendation",
            "",
            summary["recommendation"],
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MISMATCH_DIR.mkdir(parents=True, exist_ok=True)

    build_results = builder.build_all(PRED_DIR)
    table_rows = []
    run_outputs = []
    embeddings = {"available": None, "reason": ""}

    for dataset, csv_path in DATASETS.items():
        for variant, spec in VARIANTS.items():
            exact_metrics, exact_mismatch, exact_report = run_exact(dataset, variant, csv_path, spec)
            table_rows.append(metric_row(dataset, variant, "exact", exact_metrics))
            run_outputs.append({"dataset": dataset, "variant": variant, "mode": "exact", "mismatches": str(exact_mismatch), "report": str(exact_report)})
            for matcher in ["difflib", "embedding"]:
                soft_metrics, soft_mismatch, soft_report = run_soft(dataset, variant, csv_path, spec, matcher)
                if matcher == "embedding":
                    embeddings["available"] = soft_metrics.get("entity_matcher_available", False)
                    embeddings["reason"] = soft_metrics.get("entity_matcher_reason", "")
                table_rows.append(metric_row(dataset, variant, f"soft-{matcher}", soft_metrics))
                run_outputs.append(
                    {
                        "dataset": dataset,
                        "variant": variant,
                        "mode": f"soft-{matcher}",
                        "mismatches": str(soft_mismatch),
                        "report": str(soft_report),
                    }
                )

    by_key = {(row["dataset"], row["variant"], row["metric_mode"]): row for row in table_rows}
    in_v2 = by_key[("in_domain_dev", "V2", "exact")]
    in_onto = by_key[("in_domain_dev", "V_ontology", "exact")]
    tb_v2_exact = by_key[("true_blind_R6", "V2", "exact")]
    tb_v2_soft = by_key[("true_blind_R6", "V2", "soft-embedding")]
    diag_soft = by_key[("true_blind_R6", "DIAGNOSTIC_gold_other_V2", "soft-embedding")]
    strict_moves = any(row["strict"] > 0.02 for row in table_rows)
    verdicts = {
        "in_domain_no_regression": in_v2["relaxed_1"] + 0.02 >= in_onto["relaxed_1"],
        "soft_metric_unlocks_transfer": tb_v2_soft["relaxed_1"] > 0.05 and approx_zero(tb_v2_exact["relaxed_1"]),
        "entities_sufficient_for_relaxed": diag_soft["relaxed_1"] >= 0.5,
        "strict_moves": strict_moves,
    }
    if verdicts["soft_metric_unlocks_transfer"] and verdicts["entities_sufficient_for_relaxed"]:
        recommendation = "Soft entity scoring is warranted for relaxed full-row reads; next work should target role/status/relation/answer errors because V2 entities permit many relaxed rows when other fields are correct."
    elif verdicts["soft_metric_unlocks_transfer"]:
        recommendation = "Soft entity scoring moves transfer off zero, but entities still cap relaxed rows; improve V2 recall/precision before treating route fields as the main bottleneck."
    else:
        recommendation = "V2 entity swap does not unlock full-row relaxed scores enough; keep entity metric/extractor development ahead of route-field work."

    summary = {
        "experiment": "full_extraction_with_v2_entities",
        "build_results": build_results,
        "embeddings": embeddings,
        "table_rows": table_rows,
        "role_accuracy_constant": role_accuracy_flags(table_rows),
        "verdicts": verdicts,
        "recommendation": recommendation,
        "run_outputs": run_outputs,
        "outputs": {"report": str(REPORT_PATH), "summary": str(SUMMARY_PATH)},
    }
    write_report(summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("full_extraction_with_v2_entities")
    print(f"embeddings_available={embeddings['available']} reason={embeddings['reason']}")
    columns = ["variant", "metric_mode", "entity_avg_jaccard", "strict", "relaxed_1", "relaxed_2", "relaxed_3", "role_accuracy"]
    for dataset in DATASETS:
        print(f"\n{dataset}")
        print(markdown_table([row for row in table_rows if row["dataset"] == dataset], columns))
    print("verdicts=" + json.dumps(verdicts, sort_keys=True))
    print(f"report={REPORT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
