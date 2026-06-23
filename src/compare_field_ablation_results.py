import csv
import re
from pathlib import Path


REPORT_DIR = Path("data/v1/hybrid/field_ablation/reports")
VARIANT_CSV = Path("data/v1/gold/full_extraction_variant_comparison.csv")
OLLAMA_REPORT = Path("data/v1/llm_eval/reports/ollama_llama31_full_v2_evaluation.md")
HYBRID_REPORT = Path("data/v1/hybrid/reports/ollama_role_ontology_entity_v1_evaluation.md")
OUT_MD = REPORT_DIR / "FIELD_ABLATION_COMPARISON.md"
OUT_CSV = REPORT_DIR / "field_ablation_comparison.csv"

ABLATION_VARIANTS = [
    "A_ollama_role_ontology_entities_ollama_other",
    "B_add_combined_status",
    "C_add_combined_relation",
    "D_add_combined_answer",
    "E_combined_status_relation_answer",
]

METRICS = [
    "role_accuracy",
    "entity_jaccard",
    "entity_exact",
    "operative_status_accuracy",
    "relation_accuracy",
    "answer_relevance_accuracy",
    "strict_full_row",
    "relaxed_1",
    "relaxed_2",
    "relaxed_3",
]

MD_METRIC_KEYS = {
    "role accuracy": "role_accuracy",
    "entity average Jaccard": "entity_jaccard",
    "entity exact match": "entity_exact",
    "operative status accuracy": "operative_status_accuracy",
    "relation accuracy": "relation_accuracy",
    "answer relevance accuracy": "answer_relevance_accuracy",
    "strict full-row accuracy": "strict_full_row",
    "relaxed_1": "relaxed_1",
    "relaxed_2": "relaxed_2",
    "relaxed_3": "relaxed_3",
}


def parse_markdown_metrics(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing report: {path}")
    metrics = {}
    row_pattern = re.compile(r"^\|\s*(.*?)\s*\|\s*([0-9.]+)\s*\|$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = row_pattern.match(line.strip())
        if not match:
            continue
        raw_key, raw_value = match.groups()
        key = MD_METRIC_KEYS.get(raw_key)
        if key:
            metrics[key] = float(raw_value)
    missing = [metric for metric in METRICS if metric not in metrics]
    if missing:
        raise ValueError(f"Report {path} missing metrics: {', '.join(missing)}")
    return metrics


def read_variant_metrics():
    if not VARIANT_CSV.exists():
        raise FileNotFoundError(f"Missing variant comparison CSV: {VARIANT_CSV}")
    with VARIANT_CSV.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    by_variant = {row["variant"]: row for row in rows}
    required = ["ontology_only", "combined_v3"]
    missing = [name for name in required if name not in by_variant]
    if missing:
        raise ValueError(f"{VARIANT_CSV} missing variants: {', '.join(missing)}")
    return by_variant


def variant_csv_metrics(row):
    return {
        "role_accuracy": float(row["role_accuracy"]),
        "entity_jaccard": float(row["entity_jaccard"]),
        "entity_exact": float(row["entity_exact"]),
        "operative_status_accuracy": "",
        "relation_accuracy": float(row["relation_accuracy"]),
        "answer_relevance_accuracy": float(row["answer_relevance_accuracy"]),
        "strict_full_row": float(row["strict_full_row"]),
        "relaxed_1": float(row["relaxed_1"]),
        "relaxed_2": float(row["relaxed_2"]),
        "relaxed_3": float(row["relaxed_3"]),
    }


def fmt(value):
    if value == "":
        return ""
    return f"{value:.3f}"


def collect_rows():
    variant_rows = read_variant_metrics()
    rows = [
        {"variant": "ollama_full_v2", **parse_markdown_metrics(OLLAMA_REPORT)},
        {"variant": "ontology_v1_entity_baseline", **variant_csv_metrics(variant_rows["ontology_only"])},
        {"variant": "combined_v3", **variant_csv_metrics(variant_rows["combined_v3"])},
        {
            "variant": "previous_hybrid_ollama_role_ontology_entity",
            **parse_markdown_metrics(HYBRID_REPORT),
        },
    ]
    for variant in ABLATION_VARIANTS:
        report_path = REPORT_DIR / f"{variant}_evaluation.md"
        rows.append({"variant": variant, **parse_markdown_metrics(report_path)})
    return rows


def write_csv(rows):
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["variant", *METRICS])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows):
    previous = next(row for row in rows if row["variant"] == "previous_hybrid_ollama_role_ontology_entity")
    combined = next(row for row in rows if row["variant"] == "combined_v3")
    best_relaxed_1 = max(rows, key=lambda row: row["relaxed_1"])
    best_relaxed_2 = max(rows, key=lambda row: row["relaxed_2"])
    best_relaxed_3 = max(rows, key=lambda row: row["relaxed_3"])
    e_row = next(row for row in rows if row["variant"] == "E_combined_status_relation_answer")

    lines = [
        "# Field Ablation Comparison",
        "",
        "## Metrics",
        "",
        "| variant | role | entity_jaccard | entity_exact | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + row["variant"]
            + " | "
            + " | ".join(fmt(row[metric]) for metric in METRICS)
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"Previous hybrid relaxed scores were {fmt(previous['relaxed_1'])} / {fmt(previous['relaxed_2'])} / {fmt(previous['relaxed_3'])}.",
            f"Variant E relaxed scores are {fmt(e_row['relaxed_1'])} / {fmt(e_row['relaxed_2'])} / {fmt(e_row['relaxed_3'])}.",
            f"Combined_v3 relaxed scores are {fmt(combined['relaxed_1'])} / {fmt(combined['relaxed_2'])} / {fmt(combined['relaxed_3'])}.",
            f"Best relaxed_1: {best_relaxed_1['variant']} = {fmt(best_relaxed_1['relaxed_1'])}.",
            f"Best relaxed_2: {best_relaxed_2['variant']} = {fmt(best_relaxed_2['relaxed_2'])}.",
            f"Best relaxed_3: {best_relaxed_3['variant']} = {fmt(best_relaxed_3['relaxed_3'])}.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_table(rows):
    header = [
        "variant",
        "role",
        "entity_jaccard",
        "strict",
        "relaxed_1",
        "relaxed_2",
        "relaxed_3",
    ]
    print(",".join(header))
    for row in rows:
        print(
            ",".join(
                [
                    row["variant"],
                    fmt(row["role_accuracy"]),
                    fmt(row["entity_jaccard"]),
                    fmt(row["strict_full_row"]),
                    fmt(row["relaxed_1"]),
                    fmt(row["relaxed_2"]),
                    fmt(row["relaxed_3"]),
                ]
            )
        )


def main():
    rows = collect_rows()
    write_csv(rows)
    write_markdown(rows)
    print_table(rows)
    print(f"comparison_md={OUT_MD}")
    print(f"comparison_csv={OUT_CSV}")


if __name__ == "__main__":
    main()
