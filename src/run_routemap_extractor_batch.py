import argparse
import csv
from pathlib import Path

from entity_ontology_v1 import format_entity_set
from routemap_extractor_provider import make_provider


PRED_COLUMNS = [
    "pred_role",
    "pred_entities",
    "pred_operative_status",
    "pred_relation",
    "pred_answer_relevant",
    "pred_rationale",
]


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["stub", "rule", "prompt_only"], required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    rows = read_rows(args.in_path)
    if args.limit:
        rows = rows[: args.limit]
    provider = make_provider(args.provider)
    fieldnames = list(rows[0].keys()) + [column for column in PRED_COLUMNS if column not in rows[0]]
    output = []
    for row in rows:
        extraction = provider.extract(row.get("text", ""), row.get("title", ""))
        out = dict(row)
        out["pred_role"] = extraction["role"]
        out["pred_entities"] = format_entity_set(set(extraction["entities"]))
        out["pred_operative_status"] = extraction["operative_status"]
        out["pred_relation"] = extraction["relation"]
        out["pred_answer_relevant"] = extraction["answer_relevant"]
        out["pred_rationale"] = extraction["rationale"]
        output.append(out)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output)
    print(f"Provider: {args.provider}")
    print(f"Rows written: {len(output)}")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
