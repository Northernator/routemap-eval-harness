import csv
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import format_entity_set, split_entity_set


INPUT_PATH = Path("data/v1/gold/entity_extraction_predictions_fresh.csv")
OUT_MD = Path("data/v1/gold/ENTITY_ERROR_ANALYSIS_FRESH.md")
OUT_CSV = Path("data/v1/gold/entity_error_analysis_fresh.csv")


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def jaccard(gold, pred):
    return safe_div(len(gold & pred), len(gold | pred))


def classify_row(row):
    gold = split_entity_set(row.get("gold_entities", ""))
    current = split_entity_set(row.get("pred_entities_current", ""))
    ontology = split_entity_set(row.get("pred_entities_ontology_v1", ""))
    current_score = jaccard(gold, current)
    ontology_score = jaccard(gold, ontology)
    zero_current = not (gold & current)
    zero_ontology = not (gold & ontology)

    if zero_current and zero_ontology:
        category = "both_zero_overlap"
    elif ontology_score > current_score:
        category = "ontology_v1_wins"
    elif current_score > ontology_score:
        category = "current_extractor_wins"
    elif current_score == 0 and ontology_score == 0:
        category = "both_fail"
    else:
        category = "tie"

    return {
        "segment_id": row.get("segment_id", ""),
        "title": row.get("title", ""),
        "text": row.get("text", ""),
        "gold_entities": format_entity_set(gold),
        "pred_entities_current": format_entity_set(current),
        "pred_entities_ontology_v1": format_entity_set(ontology),
        "current_jaccard": f"{current_score:.6f}",
        "ontology_v1_jaccard": f"{ontology_score:.6f}",
        "category": category,
        "current_missing": format_entity_set(gold - current),
        "ontology_missing": format_entity_set(gold - ontology),
        "current_extra": format_entity_set(current - gold),
        "ontology_extra": format_entity_set(ontology - gold),
        "zero_overlap_current": "YES" if zero_current else "NO",
        "zero_overlap_ontology_v1": "YES" if zero_ontology else "NO",
    }


def recommended_additions(missing):
    recommendations = []
    for entity, count in missing.most_common(12):
        recommendations.append((entity, count, f"Add or broaden triggers for `{entity}` using fresh error rows before any future non-test tuning."))
    return recommendations


def main():
    rows = read_rows(INPUT_PATH)
    analysis_rows = [classify_row(row) for row in rows]
    category_counts = Counter(row["category"] for row in analysis_rows)
    ontology_missing = Counter()
    ontology_extra = Counter()
    current_missing = Counter()
    current_extra = Counter()

    for row in analysis_rows:
        ontology_missing.update(split_entity_set(row["ontology_missing"]))
        ontology_extra.update(split_entity_set(row["ontology_extra"]))
        current_missing.update(split_entity_set(row["current_missing"]))
        current_extra.update(split_entity_set(row["current_extra"]))

    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        fieldnames = list(analysis_rows[0].keys()) if analysis_rows else []
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analysis_rows)

    lines = [
        "# Entity Error Analysis on Fresh Adjudicated Test",
        "",
        "## Row Categories",
        "",
        "| category | rows |",
        "|---|---:|",
    ]
    for category, count in category_counts.most_common():
        lines.append(f"| {category} | {count} |")
    lines.extend(["", "## Zero-Overlap Rows", "", "| segment_id | current_zero | ontology_zero | gold | current | ontology_v1 |", "|---|---|---|---|---|---|"])
    for row in analysis_rows:
        if row["zero_overlap_current"] == "YES" or row["zero_overlap_ontology_v1"] == "YES":
            lines.append(
                f"| {row['segment_id']} | {row['zero_overlap_current']} | {row['zero_overlap_ontology_v1']} | "
                f"{row['gold_entities']} | {row['pred_entities_current']} | {row['pred_entities_ontology_v1']} |"
            )
    lines.extend(["", "## Rows Where Current Extractor Wins", "", "| segment_id | current J | ontology J | gold |", "|---|---:|---:|---|"])
    for row in analysis_rows:
        if row["category"] == "current_extractor_wins":
            lines.append(f"| {row['segment_id']} | {float(row['current_jaccard']):.3f} | {float(row['ontology_v1_jaccard']):.3f} | {row['gold_entities']} |")
    lines.extend(["", "## Rows Where Ontology V1 Wins", "", "| segment_id | current J | ontology J | gold |", "|---|---:|---:|---|"])
    for row in analysis_rows:
        if row["category"] == "ontology_v1_wins":
            lines.append(f"| {row['segment_id']} | {float(row['current_jaccard']):.3f} | {float(row['ontology_v1_jaccard']):.3f} | {row['gold_entities']} |")
    lines.extend(["", "## Ontology V1 Missing Entities", "", "| entity | count |", "|---|---:|"])
    for entity, count in ontology_missing.most_common(20):
        lines.append(f"| {entity} | {count} |")
    lines.extend(["", "## Ontology V1 Extra Entities", "", "| entity | count |", "|---|---:|"])
    for entity, count in ontology_extra.most_common(20):
        lines.append(f"| {entity} | {count} |")
    lines.extend(["", "## Recommended Ontology Additions", "", "| entity | missing count | recommendation |", "|---|---:|---|"])
    for entity, count, recommendation in recommended_additions(ontology_missing):
        lines.append(f"| {entity} | {count} | {recommendation} |")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Rows: {len(rows)}")
    for category, count in category_counts.most_common():
        print(f"{category}: {count}")
    print(f"Markdown: {OUT_MD}")
    print(f"CSV: {OUT_CSV}")


if __name__ == "__main__":
    main()
