import argparse
import csv
import re
from pathlib import Path


DEFAULT_OLLAMA_MD = Path("data/v1/llm_eval/reports/ollama_llama31_full_v2_evaluation.md")
DEFAULT_VARIANTS = Path("data/v1/gold/full_extraction_variant_comparison.csv")
DEFAULT_HYBRID_MD = Path("data/v1/hybrid/reports/ollama_role_ontology_entity_v1_evaluation.md")
DEFAULT_OUT_MD = Path("data/v1/hybrid/reports/ollama_role_ontology_entity_v1_comparison.md")
DEFAULT_OUT_CSV = Path("data/v1/hybrid/reports/ollama_role_ontology_entity_v1_comparison.csv")

FIELDS = [
    "variant",
    "role_accuracy",
    "entity_jaccard",
    "entity_exact",
    "relation_accuracy",
    "answer_relevance_accuracy",
    "strict_full_row",
    "relaxed_1",
    "relaxed_2",
    "relaxed_3",
]


def parse_md_metrics(path):
    metrics = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        match = re.match(r"\| ([^|]+) \| ([0-9.]+) \|", line.strip())
        if match:
            metrics[match.group(1).strip()] = float(match.group(2))
    return metrics


def read_variant_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return {row["variant"]: row for row in csv.DictReader(source)}


def from_md(name, metrics):
    return {
        "variant": name,
        "role_accuracy": metrics.get("role accuracy", 0.0),
        "entity_jaccard": metrics.get("entity average Jaccard", 0.0),
        "entity_exact": metrics.get("entity exact match", 0.0),
        "relation_accuracy": metrics.get("relation accuracy", 0.0),
        "answer_relevance_accuracy": metrics.get("answer relevance accuracy", 0.0),
        "strict_full_row": metrics.get("strict full-row accuracy", 0.0),
        "relaxed_1": metrics.get("relaxed_1", 0.0),
        "relaxed_2": metrics.get("relaxed_2", 0.0),
        "relaxed_3": metrics.get("relaxed_3", 0.0),
    }


def from_variant_row(name, row):
    return {
        "variant": name,
        "role_accuracy": float(row["role_accuracy"]),
        "entity_jaccard": float(row["entity_jaccard"]),
        "entity_exact": float(row["entity_exact"]),
        "relation_accuracy": float(row["relation_accuracy"]),
        "answer_relevance_accuracy": float(row["answer_relevance_accuracy"]),
        "strict_full_row": float(row["strict_full_row"]),
        "relaxed_1": float(row["relaxed_1"]),
        "relaxed_2": float(row["relaxed_2"]),
        "relaxed_3": float(row["relaxed_3"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ollama-md", default=str(DEFAULT_OLLAMA_MD))
    parser.add_argument("--variants-csv", default=str(DEFAULT_VARIANTS))
    parser.add_argument("--hybrid-md", default=str(DEFAULT_HYBRID_MD))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD))
    parser.add_argument("--out-csv", default=str(DEFAULT_OUT_CSV))
    args = parser.parse_args()

    variants = read_variant_csv(args.variants_csv)
    rows = [
        from_md("ollama_full_v2", parse_md_metrics(args.ollama_md)),
        from_variant_row("ontology_v1_entity_baseline", variants["ontology_only"]),
        from_variant_row("combined_v3", variants["combined_v3"]),
        from_md("ollama_role_ontology_entity_v1", parse_md_metrics(args.hybrid_md)),
    ]

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: (f"{value:.6f}" if isinstance(value, float) else value) for key, value in row.items()})

    lines = [
        "# Hybrid Role/Ontology Entity Comparison",
        "",
        "| variant | role acc | entity Jaccard | entity exact | relation acc | answer relevance | strict | relaxed_1 | relaxed_2 | relaxed_3 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['variant']} | {row['role_accuracy']:.3f} | {row['entity_jaccard']:.3f} | "
            f"{row['entity_exact']:.3f} | {row['relation_accuracy']:.3f} | "
            f"{row['answer_relevance_accuracy']:.3f} | {row['strict_full_row']:.3f} | "
            f"{row['relaxed_1']:.3f} | {row['relaxed_2']:.3f} | {row['relaxed_3']:.3f} |"
        )
    hybrid = rows[-1]
    ollama = rows[0]
    combined = rows[2]
    lines.extend([
        "",
        "## Interpretation",
        "",
        f"The hybrid preserves Ollama role accuracy at {hybrid['role_accuracy']:.3f} versus Ollama full v2 {ollama['role_accuracy']:.3f}.",
        f"Entity Jaccard moves from Ollama full v2 {ollama['entity_jaccard']:.3f} toward ontology_v1 at {hybrid['entity_jaccard']:.3f}.",
        f"Relaxed_1 changes from {ollama['relaxed_1']:.3f} to {hybrid['relaxed_1']:.3f}; combined_v3 remains {combined['relaxed_1']:.3f}.",
    ])
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("Comparison table:")
    for row in rows:
        print(
            f"{row['variant']}: role={row['role_accuracy']:.3f} entity_jaccard={row['entity_jaccard']:.3f} "
            f"strict={row['strict_full_row']:.3f} relaxed_1={row['relaxed_1']:.3f} "
            f"relaxed_2={row['relaxed_2']:.3f} relaxed_3={row['relaxed_3']:.3f}"
        )
    print(f"Markdown: {out_md}")
    print(f"CSV: {out_csv}")


if __name__ == "__main__":
    main()
