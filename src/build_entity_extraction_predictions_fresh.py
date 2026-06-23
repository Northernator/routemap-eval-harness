import csv
from pathlib import Path

from entity_ontology_v1 import extract_entities_ontology_v1


GOLD_PATH = Path("data/v1/gold/model_test_fresh_adjudicated_role.csv")
PRED_PATH = Path("data/v1/gold/heldout_full_extraction_pred_v2_fresh_adjudicated.csv")
OUT_PATH = Path("data/v1/gold/entity_extraction_predictions_fresh.csv")

FIELDNAMES = [
    "segment_id",
    "title",
    "text",
    "gold_entities",
    "pred_entities_current",
    "pred_entities_ontology_v1",
]


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def main():
    gold_rows = read_rows(GOLD_PATH)
    pred_rows = {row["segment_id"]: row for row in read_rows(PRED_PATH)}
    output_rows = []
    missing = []

    for row in gold_rows:
        segment_id = row["segment_id"]
        pred_row = pred_rows.get(segment_id)
        if pred_row is None:
            missing.append(segment_id)
            continue
        output_rows.append({
            "segment_id": segment_id,
            "title": row.get("title", ""),
            "text": row.get("text", ""),
            "gold_entities": row.get("gold_entities", ""),
            "pred_entities_current": pred_row.get("pred_entities", ""),
            "pred_entities_ontology_v1": extract_entities_ontology_v1(row.get("text", ""), row.get("title", "")),
        })

    if missing:
        raise ValueError(f"Missing current predictions for {len(missing)} rows: {missing[:5]}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Rows written: {len(output_rows)}")
    print(f"Output: {OUT_PATH}")


if __name__ == "__main__":
    main()
