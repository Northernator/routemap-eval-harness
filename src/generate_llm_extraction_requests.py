import argparse
import csv
import json
from pathlib import Path

from routemap_extraction_contract import (
    ALLOWED_ANSWER_RELEVANCE,
    ALLOWED_RELATIONS,
    ALLOWED_ROLES,
    ALLOWED_STATUSES,
)


TEMPLATE_PATH = Path("data/v1/gold/ROUTEMAP_LLM_EXTRACTION_PROMPT_TEMPLATE.md")


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def build_prompt(template, title, text):
    return (
        f"{template.rstrip()}\n\n"
        "Return JSON only. Do not include markdown fences or commentary.\n\n"
        f"Title: {title}\n"
        f"Text: {text}\n"
        "Output JSON:"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    rows = read_rows(args.in_path)
    if args.limit:
        rows = rows[: args.limit]
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    contract = {
        "role": f"one of {ALLOWED_ROLES}",
        "entities": ["canonical entity strings"],
        "operative_status": f"one of {ALLOWED_STATUSES}",
        "relation": f"one of {ALLOWED_RELATIONS}",
        "answer_relevant": "/".join(ALLOWED_ANSWER_RELEVANCE),
        "rationale": "short explanation",
    }
    with out_path.open("w", encoding="utf-8", newline="\n") as target:
        for row in rows:
            record = {
                "segment_id": row["segment_id"],
                "title": row.get("title", ""),
                "text": row.get("text", ""),
                "prompt": build_prompt(template, row.get("title", ""), row.get("text", "")),
                "expected_output_contract": contract,
            }
            target.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Rows written: {len(rows)}")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
