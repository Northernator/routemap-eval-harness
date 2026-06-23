import csv
import sys
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import split_entity_set
from role_taxonomies import ALLOWED_FINE_ROLES


ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold.csv"

REQUIRED_COLUMNS = [
    "doc_id",
    "segment_id",
    "source_doc",
    "title",
    "segment_index",
    "segment_text",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
]

VALID_ROLES = set(ALLOWED_FINE_ROLES)
VALID_STATUS = {"ACTIVE", "CONDITIONAL", "LIMITED", "NEGATED", "DESCRIPTIVE"}
VALID_RELATIONS = {
    "asserts",
    "defines",
    "gives_example",
    "limits",
    "maps_to",
    "proposes_next_test",
    "recommends",
    "reports_usefulness",
    "sets_context",
    "supports_retrieval",
    "warns_about",
    "requires",
}
VALID_ANSWERS = {"YES", "NO", "MAYBE"}


def clean(value):
    return "" if value is None else str(value).strip()


def read_rows(path):
    if not path.exists():
        raise ValueError(f"Missing human annotation file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
        return list(reader)


def validate_rows(rows):
    errors = []
    seen = set()
    counts = {
        "role": Counter(),
        "status": Counter(),
        "relation": Counter(),
        "answer": Counter(),
    }
    for row_number, row in enumerate(rows, start=2):
        segment_id = clean(row.get("segment_id"))
        role = clean(row.get("gold_role"))
        status = clean(row.get("gold_operative_status"))
        relation = clean(row.get("gold_relation"))
        answer = clean(row.get("gold_answer_relevant"))
        text = clean(row.get("text")) or clean(row.get("segment_text"))

        if not segment_id:
            errors.append(f"row {row_number}: missing segment_id")
        elif segment_id in seen:
            errors.append(f"row {row_number}: duplicated segment_id {segment_id}")
        seen.add(segment_id)

        if not text:
            errors.append(f"row {row_number} segment {segment_id or '(blank)'}: missing text/segment_text")
        if role not in VALID_ROLES:
            errors.append(f"row {row_number} segment {segment_id}: invalid gold_role {role!r}")
        if status not in VALID_STATUS:
            errors.append(f"row {row_number} segment {segment_id}: invalid gold_operative_status {status!r}")
        if relation not in VALID_RELATIONS:
            errors.append(f"row {row_number} segment {segment_id}: invalid gold_relation {relation!r}")
        if answer not in VALID_ANSWERS:
            errors.append(f"row {row_number} segment {segment_id}: invalid gold_answer_relevant {answer!r}")
        try:
            split_entity_set(clean(row.get("gold_entities")))
        except Exception as exc:
            errors.append(f"row {row_number} segment {segment_id}: gold_entities parse error: {exc}")

        counts["role"][role or "(blank)"] += 1
        counts["status"][status or "(blank)"] += 1
        counts["relation"][relation or "(blank)"] += 1
        counts["answer"][answer or "(blank)"] += 1

    return errors, counts


def print_counts(counts):
    for label, counter in counts.items():
        print(f"{label}_counts")
        for key, count in sorted(counter.items()):
            print(f"- {key}: {count}")


def validate(path=GOLD):
    rows = read_rows(path)
    if not rows:
        raise ValueError(f"No rows found in human annotation file: {path}")
    errors, counts = validate_rows(rows)
    print(f"row_count={len(rows)}")
    print_counts(counts)
    if errors:
        print("gold_validation_result=FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("gold_validation_result=PASS")
    return rows


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else GOLD
    validate(path)


if __name__ == "__main__":
    main()
