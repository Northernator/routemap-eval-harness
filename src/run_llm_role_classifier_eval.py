"""Evaluate LLM role classifier against a seed-train deterministic baseline."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from role_taxonomies import ALLOWED_FINE_ROLES, available_taxonomies, map_role
from train_role_text_baselines import CentroidTfidfLike


ROOT = Path(__file__).resolve().parents[1]
TRAIN_DEV_PATH = ROOT / "data/v1/gold/model_train_dev_role.csv"
TRUE_BLIND_PATH = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
OUT_DIR = ROOT / "data/v1/role_experiments/llm_role_classifier"
OUTPUT_DIR = OUT_DIR / "outputs"
PRED_DIR = OUT_DIR / "predictions"
REPORT_DIR = OUT_DIR / "reports"
SUMMARY_PATH = OUT_DIR / "SUMMARY.json"
REPORT_PATH = OUT_DIR / "ROLE_LLM_CLASSIFIER_REPORT.md"
SCORER = ROOT / "src/evaluate_role_taxonomy_levels.py"

DEV_CACHE = OUTPUT_DIR / "dev_roles.jsonl"
TRUE_BLIND_CACHE = OUTPUT_DIR / "true_blind_roles.jsonl"
DATASETS = {
    "dev": {
        "cache": DEV_CACHE,
        "prediction": PRED_DIR / "dev_role_predictions.csv",
        "score_md": REPORT_DIR / "dev_role_taxonomy_eval.md",
        "score_csv": REPORT_DIR / "dev_role_taxonomy_eval.csv",
    },
    "true_blind": {
        "cache": TRUE_BLIND_CACHE,
        "prediction": PRED_DIR / "true_blind_role_predictions.csv",
        "score_md": REPORT_DIR / "true_blind_role_taxonomy_eval.md",
        "score_csv": REPORT_DIR / "true_blind_role_taxonomy_eval.csv",
    },
}

ROLES = list(ALLOWED_FINE_ROLES)
HARD_PAIRS = [
    ("CLAIM", "DEFINE"),
    ("DEFINE", "CLAIM"),
    ("RESULT", "CLAIM"),
    ("CLAIM", "RESULT"),
    ("BACKGROUND", "CLAIM"),
    ("CLAIM", "BACKGROUND"),
]


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_rows(path, rows, fieldnames):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def train_dev_rows():
    rows = read_rows(TRAIN_DEV_PATH)
    return [row for row in rows if row.get("split") == "seed_train"], [
        row for row in rows if row.get("split") == "heldout_v1_dev"
    ]


def dataset_source_rows(dataset):
    train_rows, dev_rows = train_dev_rows()
    if dataset == "dev":
        return train_rows, dev_rows
    if dataset == "true_blind":
        return train_rows, read_rows(TRUE_BLIND_PATH)
    raise ValueError(dataset)


def read_cache(path):
    if not Path(path).exists():
        raise SystemExit(f"Missing LLM role cache: {path}. Run run_llm_role_classifier.py first.")
    cache = {}
    with Path(path).open("r", encoding="utf-8-sig") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            segment_id = row.get("segment_id", "")
            if segment_id:
                cache[segment_id] = row
    return cache


def wrong_role(gold):
    for role in ROLES:
        if role != gold:
            return role
    return ROLES[0]


def llm_role_for(row, cached):
    role = str(cached.get("pred_role", "")).strip().upper() if cached else ""
    if role in ROLES and not cached.get("parse_failed") and not cached.get("invalid_label"):
        return role
    return wrong_role(row.get("gold_role", ""))


def build_predictions(dataset, model):
    _train_rows, rows = dataset_source_rows(dataset)
    cache = read_cache(DATASETS[dataset]["cache"])
    missing = [row.get("segment_id", "") for row in rows if row.get("segment_id", "") not in cache]
    if missing:
        raise SystemExit(f"Missing cached LLM role rows for {dataset}: {', '.join(missing[:10])}")
    output = []
    parse_failed = 0
    invalid = 0
    for row in rows:
        segment_id = row.get("segment_id", "")
        cached = cache[segment_id]
        parse_failed += int(bool(cached.get("parse_failed")))
        invalid += int(bool(cached.get("invalid_label")))
        copied = dict(row)
        copied["pred_role_baseline"] = model.predict({"text": row.get("text") or row.get("segment_text") or ""})
        copied["pred_role_llm_raw"] = cached.get("pred_role", "")
        copied["pred_role_llm"] = llm_role_for(row, cached)
        copied["llm_parse_failed"] = str(bool(cached.get("parse_failed")))
        copied["llm_invalid_label"] = cached.get("invalid_label", "")
        output.append(copied)
    fieldnames = list(output[0].keys()) if output else []
    write_rows(DATASETS[dataset]["prediction"], output, fieldnames)
    return {
        "dataset": dataset,
        "rows": len(output),
        "cache_rows": len(cache),
        "parse_failed": parse_failed,
        "invalid_label": invalid,
        "parse_invalid_rate": (parse_failed + invalid) / len(output) if output else 0.0,
        "prediction": str(DATASETS[dataset]["prediction"]),
    }


def run_scorer(dataset):
    spec = DATASETS[dataset]
    cmd = [
        sys.executable,
        str(SCORER),
        "--csv",
        str(spec["prediction"]),
        "--gold-col",
        "gold_role",
        "--pred-cols",
        "pred_role_llm",
        "pred_role_baseline",
        "--out-md",
        str(spec["score_md"]),
        "--out-csv",
        str(spec["score_csv"]),
    ]
    subprocess.run(cmd, check=True)


def read_score_csv(path, dataset):
    rows = read_rows(path)
    seen = set()
    output = []
    for row in rows:
        key = (row["model_name"], row["taxonomy"])
        if key in seen:
            continue
        seen.add(key)
        output.append(
            {
                "dataset": dataset,
                "model": "llm" if row["model_name"] == "pred_role_llm" else "baseline",
                "taxonomy": row["taxonomy"],
                "accuracy": float(row["accuracy"]),
            }
        )
    return output


def confusion_counts(rows, pred_col):
    matrix = defaultdict(Counter)
    for row in rows:
        matrix[row.get("gold_role", "")][row.get(pred_col, "")] += 1
    return matrix


def write_confusion_csv(path, matrix):
    rows = []
    for gold in ROLES:
        for pred in ROLES:
            rows.append({"gold": gold, "pred": pred, "count": matrix[gold].get(pred, 0)})
    write_rows(path, rows, ["gold", "pred", "count"])


def hard_pair_rows(dataset, rows):
    output = []
    for model_name, pred_col in [("llm", "pred_role_llm"), ("baseline", "pred_role_baseline")]:
        matrix = confusion_counts(rows, pred_col)
        write_confusion_csv(REPORT_DIR / f"{dataset}__{model_name}__fine8_confusion.csv", matrix)
        for gold, pred in HARD_PAIRS:
            output.append(
                {
                    "dataset": dataset,
                    "model": model_name,
                    "gold": gold,
                    "pred": pred,
                    "count": matrix[gold].get(pred, 0),
                }
            )
    return output


def accuracy_lookup(table_rows):
    return {(row["dataset"], row["model"], row["taxonomy"]): row["accuracy"] for row in table_rows}


def build_verdicts(table_rows, hard_pairs):
    acc = accuracy_lookup(table_rows)
    llm_hard = sum(row["count"] for row in hard_pairs if row["model"] == "llm")
    baseline_hard = sum(row["count"] for row in hard_pairs if row["model"] == "baseline")
    return {
        "llm_beats_baseline_8role_dev": acc[("dev", "llm", "fine_8")] > acc[("dev", "baseline", "fine_8")],
        "llm_beats_baseline_outdomain_8role": acc[("true_blind", "llm", "fine_8")]
        > acc[("true_blind", "baseline", "fine_8")],
        "llm_beats_0306_outdomain_reference": acc[("true_blind", "llm", "fine_8")] > 0.306,
        "llm_coarse3_strong": acc[("dev", "llm", "coarse_3")] >= 0.75,
        "hard_pairs_reduced": llm_hard < baseline_hard,
        "hard_pair_total_llm": llm_hard,
        "hard_pair_total_baseline": baseline_hard,
    }


def fmt(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def markdown_table(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def write_report(summary):
    acc_columns = ["dataset", "model", "taxonomy", "accuracy"]
    hard_columns = ["dataset", "model", "gold", "pred", "count"]
    lines = [
        "# ROLE_LLM_CLASSIFIER_REPORT",
        "",
        "Local Ollama llama3.1, temperature 0. Prompt examples are frozen seed_train rows only. Locked fresh/adjudicated test files are not read or scored.",
        "",
        "Known prior locked-test references: centroid 8-role 0.456; coarse-3 0.810; true-blind combined/R6 role reference 0.306.",
        "",
        "## Accuracy by taxonomy",
        "",
        markdown_table(summary["accuracy_rows"], acc_columns),
        "",
        "## Hard-pair confusion counts",
        "",
        markdown_table(summary["hard_pair_rows"], hard_columns),
        "",
        "## Parse rates",
        "",
        markdown_table(summary["build_results"], ["dataset", "rows", "parse_failed", "invalid_label", "parse_invalid_rate"]),
        "",
        "## Verdicts",
        "",
        markdown_table([summary["verdicts"]], list(summary["verdicts"].keys())),
        "",
        "## Recommendation",
        "",
        summary["recommendation"],
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def recommendation(verdicts, accuracy_rows):
    acc = accuracy_lookup(accuracy_rows)
    if verdicts["llm_beats_baseline_8role_dev"] and verdicts["llm_beats_baseline_outdomain_8role"]:
        classifier = "Adopt the LLM role classifier for diagnostic runs."
    else:
        classifier = "Do not replace the deterministic baseline with the LLM yet."
    if acc[("dev", "llm", "coarse_3")] >= 0.75 and acc[("true_blind", "llm", "coarse_3")] >= acc[
        ("true_blind", "llm", "fine_8")
    ]:
        taxonomy = "Operationally, coarse_3 is the strongest taxonomy; keep fine_8 as an analysis label until hard-boundary errors shrink."
    else:
        taxonomy = "Fine_8 remains viable only with more hard-boundary repair."
    return f"{classifier} {taxonomy} Next step: inspect CLAIM/DEFINE and RESULT/CLAIM residuals, then reserve the locked fresh test for one final read."


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    train_rows, _dev_rows = train_dev_rows()
    model = CentroidTfidfLike()
    model.fit(train_rows)

    build_results = []
    accuracy_rows = []
    hard_pairs = []
    for dataset in DATASETS:
        build_results.append(build_predictions(dataset, model))
        run_scorer(dataset)
        accuracy_rows.extend(read_score_csv(DATASETS[dataset]["score_csv"], dataset))
        rows = read_rows(DATASETS[dataset]["prediction"])
        hard_pairs.extend(hard_pair_rows(dataset, rows))

    verdicts = build_verdicts(accuracy_rows, hard_pairs)
    summary = {
        "experiment": "llm_role_classifier_eval",
        "model": "llama3.1",
        "build_results": build_results,
        "accuracy_rows": accuracy_rows,
        "hard_pair_rows": hard_pairs,
        "verdicts": verdicts,
        "recommendation": recommendation(verdicts, accuracy_rows),
        "outputs": {
            "report": str(REPORT_PATH),
            "summary": str(SUMMARY_PATH),
            "predictions": str(PRED_DIR),
            "reports": str(REPORT_DIR),
        },
    }
    write_report(summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("llm_role_classifier_eval")
    for dataset in DATASETS:
        print(f"\n{dataset}")
        print(
            markdown_table(
                [row for row in accuracy_rows if row["dataset"] == dataset],
                ["model", "taxonomy", "accuracy"],
            )
        )
    print("verdicts=" + json.dumps(verdicts, sort_keys=True))
    print(f"report={REPORT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
