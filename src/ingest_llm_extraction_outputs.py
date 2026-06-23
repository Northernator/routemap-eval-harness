import argparse
import csv
from pathlib import Path

from entity_ontology_v1 import format_entity_set
from llm_output_utils import parse_extraction, read_jsonl, rows_by_segment


PRED_COLUMNS = [
    "pred_role",
    "pred_entities",
    "pred_operative_status",
    "pred_relation",
    "pred_answer_relevant",
    "pred_rationale",
    "pred_provider",
    "pred_model",
    "pred_valid",
    "pred_errors",
]


def read_gold(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--provider-name", required=True)
    args = parser.parse_args()

    gold_rows = read_gold(args.gold)
    output_rows, line_errors = rows_by_segment(read_jsonl(args.outputs))
    fieldnames = list(gold_rows[0].keys()) + [column for column in PRED_COLUMNS if column not in gold_rows[0]]
    output = []
    valid_count = 0
    missing_count = 0

    for row in gold_rows:
        out = dict(row)
        segment_id = row["segment_id"]
        if segment_id not in output_rows:
            missing_count += 1
            for column in PRED_COLUMNS:
                out[column] = ""
            out["pred_provider"] = args.provider_name
            out["pred_valid"] = "NO"
            out["pred_errors"] = "missing output"
        else:
            _, record = output_rows[segment_id]
            extraction, valid, errors = parse_extraction(record)
            valid_count += int(valid)
            out["pred_role"] = extraction["role"] if valid else ""
            out["pred_entities"] = format_entity_set(set(extraction["entities"])) if valid else ""
            out["pred_operative_status"] = extraction["operative_status"] if valid else ""
            out["pred_relation"] = extraction["relation"] if valid else ""
            out["pred_answer_relevant"] = extraction["answer_relevant"] if valid else ""
            out["pred_rationale"] = extraction["rationale"] if valid else ""
            out["pred_provider"] = record.get("provider", args.provider_name)
            out["pred_model"] = record.get("model", "")
            out["pred_valid"] = "YES" if valid else "NO"
            out["pred_errors"] = "; ".join(errors)
        output.append(out)

    if line_errors:
        print(f"Line-level output errors: {len(line_errors)}")
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output)
    print(f"Rows written: {len(output)}")
    print(f"Valid count: {valid_count}")
    print(f"Missing count: {missing_count}")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
