import csv
from pathlib import Path

from entity_ontology_v1 import extract_entities_ontology_v1
from evaluate_full_extraction_custom_cols import evaluate, read_rows


ORIGINAL_PATH = Path("data/v1/gold/heldout_full_extraction_pred_v2_fresh_adjudicated.csv")
BOUNDARY_PATH = Path("data/v1/gold/heldout_full_extraction_pred_boundary_augmented_role_fresh.csv")
COMBINED_PATH = Path("data/v1/gold/heldout_full_extraction_pred_combined_v3_fresh.csv")
OUT_MD = Path("data/v1/gold/FULL_EXTRACTION_VARIANT_COMPARISON.md")
OUT_CSV = Path("data/v1/gold/full_extraction_variant_comparison.csv")

FIELDNAMES = [
    "variant",
    "role_accuracy",
    "entity_exact",
    "entity_jaccard",
    "relation_accuracy",
    "answer_relevance_accuracy",
    "strict_full_row",
    "relaxed_1",
    "relaxed_2",
    "relaxed_3",
]


def included(rows):
    return [row for row in rows if row.get("include_in_eval", "YES") in {"", "YES"}]


def with_ontology_entities(rows):
    output = []
    for row in rows:
        clone = dict(row)
        clone["pred_entities_ontology_only"] = extract_entities_ontology_v1(row.get("text", ""), row.get("title", ""))
        output.append(clone)
    return output


def summarize(variant, metrics):
    return {
        "variant": variant,
        "role_accuracy": f"{metrics['role_accuracy']:.6f}",
        "entity_exact": f"{metrics['entity_exact_match']:.6f}",
        "entity_jaccard": f"{metrics['entity_average_jaccard']:.6f}",
        "relation_accuracy": f"{metrics['relation_accuracy']:.6f}",
        "answer_relevance_accuracy": f"{metrics['answer_relevance_accuracy']:.6f}",
        "strict_full_row": f"{metrics['strict_full_row_accuracy']:.6f}",
        "relaxed_1": f"{metrics['relaxed_1']:.6f}",
        "relaxed_2": f"{metrics['relaxed_2']:.6f}",
        "relaxed_3": f"{metrics['relaxed_3']:.6f}",
    }


def main():
    original_rows = included(read_rows(ORIGINAL_PATH))
    boundary_rows = included(read_rows(BOUNDARY_PATH))
    combined_rows = included(read_rows(COMBINED_PATH))
    ontology_rows = with_ontology_entities(original_rows)

    variants = [
        summarize("original", evaluate(original_rows, "pred_role", "pred_entities", "pred_operative_status", "pred_relation", "pred_answer_relevant")),
        summarize("boundary_role_only", evaluate(boundary_rows, "pred_role_boundary_augmented", "pred_entities", "pred_operative_status", "pred_relation_boundary_augmented", "pred_answer_relevant")),
        summarize("ontology_only", evaluate(ontology_rows, "pred_role", "pred_entities_ontology_only", "pred_operative_status", "pred_relation", "pred_answer_relevant")),
        summarize("combined_v3", evaluate(combined_rows, "pred_role_combined_v3", "pred_entities_combined_v3", "pred_operative_status_combined_v3", "pred_relation_combined_v3", "pred_answer_relevant_combined_v3")),
    ]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(variants)

    lines = [
        "# Full Extraction Variant Comparison",
        "",
        "| variant | role acc | entity exact | entity Jaccard | relation acc | answer relevance | strict | relaxed_1 | relaxed_2 | relaxed_3 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in variants:
        lines.append(
            f"| {row['variant']} | {float(row['role_accuracy']):.3f} | {float(row['entity_exact']):.3f} | "
            f"{float(row['entity_jaccard']):.3f} | {float(row['relation_accuracy']):.3f} | "
            f"{float(row['answer_relevance_accuracy']):.3f} | {float(row['strict_full_row']):.3f} | "
            f"{float(row['relaxed_1']):.3f} | {float(row['relaxed_2']):.3f} | {float(row['relaxed_3']):.3f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "Boundary-role augmentation improves role and relation fields. Ontology-only improves entity overlap but leaves role errors untouched. Combined v3 tests whether those two gains interact in full-extraction scoring without tuning either component on the fresh adjudicated test.",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("Variant comparison:")
    for row in variants:
        print(
            f"{row['variant']}: role={float(row['role_accuracy']):.3f} "
            f"entity_jaccard={float(row['entity_jaccard']):.3f} strict={float(row['strict_full_row']):.3f} "
            f"relaxed_1={float(row['relaxed_1']):.3f} relaxed_2={float(row['relaxed_2']):.3f} relaxed_3={float(row['relaxed_3']):.3f}"
        )
    print(f"Markdown: {OUT_MD}")
    print(f"CSV: {OUT_CSV}")


if __name__ == "__main__":
    main()
