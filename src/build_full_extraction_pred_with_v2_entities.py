"""Build copied full-extraction prediction CSVs with frozen hybrid v2 entities.

Inputs are read-only. Outputs live under
data/v1/full_extraction_experiments/v2_entities/predictions/.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import entity_ontology_v1
from extract_entities_hybrid_v2 import HybridV2Config, extract_entities_hybrid_v2, format_entities


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/v1/full_extraction_experiments/v2_entities/predictions"

INPUTS = {
    "in_domain_dev": ROOT / "data/v1/gold/heldout_full_extraction_pred_v2.csv",
    "true_blind_combined_v3": ROOT
    / "data/v1/true_blind_natural_language/predictions/combined_v3_true_blind_predictions.csv",
    "true_blind_R6": ROOT / "data/v1/true_blind_natural_language/predictions/R6_true_blind_predictions.csv",
}


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def row_text(row):
    return row.get("text") or row.get("segment_text") or ""


def row_title(row):
    return row.get("title") or row.get("source_topic") or ""


def write_rows(path, rows, fieldnames):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_dataset(name, source_path, out_dir=OUT_DIR):
    rows = read_rows(source_path)
    config = HybridV2Config()
    output = []
    for row in rows:
        copied = dict(row)
        text = row_text(row)
        title = row_title(row)
        copied["pred_entities_ontology"] = entity_ontology_v1.extract_entities_ontology_v1(text, title)
        copied["pred_entities_v2"] = format_entities(extract_entities_hybrid_v2(text, title, config))
        copied["pred_role_goldother"] = row.get("gold_role", "")
        copied["pred_operative_status_goldother"] = row.get("gold_operative_status", "")
        copied["pred_relation_goldother"] = row.get("gold_relation", "")
        copied["pred_answer_relevant_goldother"] = row.get("gold_answer_relevant", "")
        output.append(copied)
    fieldnames = list(rows[0].keys()) if rows else []
    for column in [
        "pred_entities_ontology",
        "pred_entities_v2",
        "pred_role_goldother",
        "pred_operative_status_goldother",
        "pred_relation_goldother",
        "pred_answer_relevant_goldother",
    ]:
        if column not in fieldnames:
            fieldnames.append(column)
    out_path = out_dir / f"{name}__with_v2_entities.csv"
    write_rows(out_path, output, fieldnames)
    return {"name": name, "source": str(source_path), "out": str(out_path), "rows": len(output)}


def build_all(out_dir=OUT_DIR):
    return [build_dataset(name, path, out_dir) for name, path in INPUTS.items()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args()
    results = build_all(Path(args.out_dir))
    print("full_extraction_with_v2_entities builder")
    for result in results:
        print(f"{result['name']}: rows={result['rows']} out={result['out']}")


if __name__ == "__main__":
    main()
