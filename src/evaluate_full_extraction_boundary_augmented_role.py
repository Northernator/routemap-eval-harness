import csv
from collections import Counter, defaultdict
from pathlib import Path


INPUT_PATH = Path("data/v1/gold/heldout_full_extraction_pred_boundary_augmented_role_fresh.csv")
RESULTS_CSV = Path("data/v1/gold/full_extraction_boundary_augmented_role_results.csv")
MISMATCH_CSV = Path("data/v1/gold/full_extraction_boundary_augmented_role_mismatches.csv")
RESULTS_MD = Path("data/v1/gold/FULL_EXTRACTION_BOUNDARY_AUGMENTED_ROLE_RESULTS.md")
TRANSFER_MD = Path("data/v1/gold/BOUNDARY_PAIR_TRANSFER_RESULTS.md")
ROLE_RESULTS_CSV = Path("data/v1/gold/boundary_augmented_role_results_fresh.csv")
TAXONOMY_RESULTS_CSV = Path("data/v1/gold/boundary_augmented_taxonomy_results_fresh.csv")

PREVIOUS_FINE = 0.456


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def split_entities(value):
    return {part.strip().lower() for part in (value or "").split(";") if part.strip()}


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def entity_jaccard(row):
    gold = split_entities(row.get("gold_entities"))
    pred = split_entities(row.get("pred_entities"))
    return safe_div(len(gold & pred), len(gold | pred))


def evaluate_variant(rows, role_col, relation_col):
    correct = Counter()
    strict = 0
    relaxed = 0
    entity_exact = 0
    jaccard_total = 0.0
    confusions = Counter()
    mismatches = []

    for row in rows:
        role_match = row.get("gold_role") == row.get(role_col)
        relation_match = row.get("gold_relation") == row.get(relation_col)
        status_match = row.get("gold_operative_status") == row.get("pred_operative_status")
        relevance_match = row.get("gold_answer_relevant") == row.get("pred_answer_relevant")
        gold_entities = split_entities(row.get("gold_entities"))
        pred_entities = split_entities(row.get("pred_entities"))
        exact_entities = gold_entities == pred_entities
        jaccard = safe_div(len(gold_entities & pred_entities), len(gold_entities | pred_entities))

        correct["role"] += int(role_match)
        correct["relation"] += int(relation_match)
        correct["operative_status"] += int(status_match)
        correct["answer_relevant"] += int(relevance_match)
        entity_exact += int(exact_entities)
        jaccard_total += jaccard

        strict_match = role_match and relation_match and status_match and relevance_match and exact_entities
        relaxed_match = role_match and relevance_match and jaccard >= 0.5
        strict += int(strict_match)
        relaxed += int(relaxed_match)

        if not role_match:
            confusions[(row.get("gold_role", ""), row.get(role_col, ""))] += 1
        if not strict_match:
            mismatches.append(row)

    total = len(rows)
    return {
        "role_accuracy": safe_div(correct["role"], total),
        "relation_accuracy": safe_div(correct["relation"], total),
        "operative_status_accuracy": safe_div(correct["operative_status"], total),
        "answer_relevance_accuracy": safe_div(correct["answer_relevant"], total),
        "entity_exact_match": safe_div(entity_exact, total),
        "entity_average_jaccard": safe_div(jaccard_total, total),
        "strict_full_row_accuracy": safe_div(strict, total),
        "relaxed_full_row_accuracy": safe_div(relaxed, total),
        "strict_mismatch_count": len(mismatches),
        "role_confusions": confusions,
        "mismatches": mismatches,
    }


def best_role_result():
    rows = [row for row in read_rows(ROLE_RESULTS_CSV) if row.get("metric_type") == "overall"]
    return max(rows, key=lambda row: float(row["accuracy"]))


def best_taxonomy_results():
    rows = read_rows(TAXONOMY_RESULTS_CSV)
    best = {}
    for row in rows:
        taxonomy = row["taxonomy"]
        if taxonomy not in best or float(row["accuracy"]) > float(best[taxonomy]["accuracy"]):
            best[taxonomy] = row
    return best


def write_results_csv(original, augmented):
    rows = [
        {"variant": "original", **{key: f"{value:.6f}" for key, value in original.items() if isinstance(value, float)}},
        {"variant": "boundary_augmented_role", **{key: f"{value:.6f}" for key, value in augmented.items() if isinstance(value, float)}},
    ]
    fieldnames = [
        "variant",
        "role_accuracy",
        "relation_accuracy",
        "operative_status_accuracy",
        "answer_relevance_accuracy",
        "entity_exact_match",
        "entity_average_jaccard",
        "strict_full_row_accuracy",
        "relaxed_full_row_accuracy",
    ]
    with RESULTS_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_mismatches(rows):
    fieldnames = [
        "segment_id",
        "title",
        "text",
        "gold_role",
        "pred_role",
        "pred_role_boundary_augmented",
        "gold_relation",
        "pred_relation",
        "pred_relation_boundary_augmented",
        "gold_entities",
        "pred_entities",
        "entity_jaccard",
        "gold_operative_status",
        "pred_operative_status",
        "gold_answer_relevant",
        "pred_answer_relevant",
    ]
    with MISMATCH_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "segment_id": row.get("segment_id", ""),
                "title": row.get("title", ""),
                "text": row.get("text", ""),
                "gold_role": row.get("gold_role", ""),
                "pred_role": row.get("pred_role", ""),
                "pred_role_boundary_augmented": row.get("pred_role_boundary_augmented", ""),
                "gold_relation": row.get("gold_relation", ""),
                "pred_relation": row.get("pred_relation", ""),
                "pred_relation_boundary_augmented": row.get("pred_relation_boundary_augmented", ""),
                "gold_entities": row.get("gold_entities", ""),
                "pred_entities": row.get("pred_entities", ""),
                "entity_jaccard": f"{entity_jaccard(row):.6f}",
                "gold_operative_status": row.get("gold_operative_status", ""),
                "pred_operative_status": row.get("pred_operative_status", ""),
                "gold_answer_relevant": row.get("gold_answer_relevant", ""),
                "pred_answer_relevant": row.get("pred_answer_relevant", ""),
            })


def format_confusions(confusions):
    if not confusions:
        return ["No remaining role confusions."]
    lines = ["| gold | pred | count |", "|---|---|---:|"]
    for (gold, pred), count in confusions.most_common(10):
        lines.append(f"| {gold} | {pred} | {count} |")
    return lines


def write_markdown(original, augmented, best_role, best_taxonomy):
    lines = [
        "# Full Extraction Boundary-Augmented Role Results",
        "",
        "## Transfer Summary",
        "",
        "| metric | original | boundary_augmented_role | delta |",
        "|---|---:|---:|---:|",
    ]
    for metric in [
        "role_accuracy",
        "relation_accuracy",
        "strict_full_row_accuracy",
        "relaxed_full_row_accuracy",
        "entity_exact_match",
        "entity_average_jaccard",
    ]:
        old = original[metric]
        new = augmented[metric]
        lines.append(f"| {metric} | {old:.3f} | {new:.3f} | {new - old:+.3f} |")
    lines.extend([
        "",
        f"Best boundary-augmented role model: `{best_role['setting']}` / `{best_role['model']}` at {float(best_role['accuracy']):.3f}.",
        "",
        "Entity predictions are unchanged in this comparison.",
        "",
        "## Remaining Boundary-Augmented Role Confusions",
        "",
    ])
    lines.extend(format_confusions(augmented["role_confusions"]))
    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")

    t = best_taxonomy
    transfer_lines = [
        "# Boundary-Pair Transfer Results",
        "",
        "## Boundary-Pair Internal Test",
        "",
        "- Setting A best accuracy without boundary training: 0.625",
        "- Setting B best accuracy with boundary training: 0.950",
        "- Improvement: +0.325",
        "",
        "## Fresh Adjudicated Transfer",
        "",
        "| taxonomy | best setting | best model | accuracy | previous best | delta |",
        "|---|---|---|---:|---:|---:|",
    ]
    for taxonomy in ["fine_8", "coarse_5", "coarse_4", "coarse_3"]:
        row = t[taxonomy]
        transfer_lines.append(
            f"| {taxonomy} | {row['setting']} | {row['model']} | {float(row['accuracy']):.3f} | "
            f"{float(row['previous_best']):.3f} | {float(row['delta']):+.3f} |"
        )
    transfer_lines.extend([
        "",
        "## Full Extraction Transfer",
        "",
        "| metric | before | after | delta |",
        "|---|---:|---:|---:|",
        f"| role_accuracy | {original['role_accuracy']:.3f} | {augmented['role_accuracy']:.3f} | {augmented['role_accuracy'] - original['role_accuracy']:+.3f} |",
        f"| strict_full_row_accuracy | {original['strict_full_row_accuracy']:.3f} | {augmented['strict_full_row_accuracy']:.3f} | {augmented['strict_full_row_accuracy'] - original['strict_full_row_accuracy']:+.3f} |",
        f"| relaxed_full_row_accuracy | {original['relaxed_full_row_accuracy']:.3f} | {augmented['relaxed_full_row_accuracy']:.3f} | {augmented['relaxed_full_row_accuracy'] - original['relaxed_full_row_accuracy']:+.3f} |",
        "",
        "## Interpretation",
        "",
    ])
    if augmented["role_accuracy"] > original["role_accuracy"]:
        transfer_lines.append("Boundary-pair training improves role transfer on the locked fresh adjudicated test, so targeted boundary examples help beyond the boundary-pair internal test.")
    else:
        transfer_lines.append("Boundary-pair training does not improve role transfer on the locked fresh adjudicated test, suggesting the boundary data is too synthetic or distribution-specific for this benchmark.")
    transfer_lines.append("Entity extraction remains a separate bottleneck because entity predictions were not changed by this role-only transfer experiment.")
    TRANSFER_MD.write_text("\n".join(transfer_lines), encoding="utf-8")


def main():
    all_rows = read_rows(INPUT_PATH)
    rows = [row for row in all_rows if row.get("include_in_eval", "YES") in {"", "YES"}]
    original = evaluate_variant(rows, "pred_role", "pred_relation")
    augmented = evaluate_variant(rows, "pred_role_boundary_augmented", "pred_relation_boundary_augmented")
    best_role = best_role_result()
    best_taxonomy = best_taxonomy_results()

    write_results_csv(original, augmented)
    write_mismatches(augmented["mismatches"])
    write_markdown(original, augmented, best_role, best_taxonomy)

    print(f"Evaluated rows: {len(rows)}")
    print(f"Original role accuracy: {original['role_accuracy']:.3f}")
    print(f"Boundary-augmented role accuracy: {augmented['role_accuracy']:.3f}")
    print(f"Original strict full-row accuracy: {original['strict_full_row_accuracy']:.3f}")
    print(f"Boundary-augmented strict full-row accuracy: {augmented['strict_full_row_accuracy']:.3f}")
    print(f"Original relaxed full-row accuracy: {original['relaxed_full_row_accuracy']:.3f}")
    print(f"Boundary-augmented relaxed full-row accuracy: {augmented['relaxed_full_row_accuracy']:.3f}")
    print(f"Entity average Jaccard: {augmented['entity_average_jaccard']:.3f}")
    print(f"Results CSV: {RESULTS_CSV}")
    print(f"Mismatches CSV: {MISMATCH_CSV}")
    print(f"Results MD: {RESULTS_MD}")
    print(f"Transfer MD: {TRANSFER_MD}")


if __name__ == "__main__":
    main()
