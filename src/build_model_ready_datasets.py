import csv
from pathlib import Path


TRAIN_SOURCES = [
    ("seed_train", Path("data/v1/gold/v1_full_extraction_gold_v1_noleak.csv")),
    ("heldout_v1_dev", Path("data/v1/gold/heldout_full_extraction_gold_v1.csv")),
]
TEST_SOURCE = Path("data/v1/gold/heldout_full_extraction_gold_v2_adjudicated.csv")
TRAIN_OUT = Path("data/v1/gold/model_train_dev_role.csv")
TEST_OUT = Path("data/v1/gold/model_test_fresh_adjudicated_role.csv")

FIELDS = [
    "split",
    "segment_id",
    "title",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
]


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def project_row(row, split):
    return {
        "split": split,
        "segment_id": row.get("segment_id", ""),
        "title": row.get("title", ""),
        "text": row.get("text", ""),
        "gold_role": row.get("gold_role", ""),
        "gold_entities": row.get("gold_entities", ""),
        "gold_operative_status": row.get("gold_operative_status", ""),
        "gold_relation": row.get("gold_relation", ""),
        "gold_answer_relevant": row.get("gold_answer_relevant", ""),
    }


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    train_rows = []
    source_counts = {}
    for split, path in TRAIN_SOURCES:
        rows = read_rows(path)
        source_counts[split] = len(rows)
        train_rows.extend(project_row(row, split) for row in rows)

    test_source_rows = read_rows(TEST_SOURCE)
    test_rows = [
        project_row(row, "fresh_v2_adjudicated_test")
        for row in test_source_rows
        if row.get("include_in_eval") == "YES"
    ]

    write_csv(TRAIN_OUT, train_rows)
    write_csv(TEST_OUT, test_rows)

    print(f"Output: {TRAIN_OUT}")
    print(f"Rows: {len(train_rows)}")
    for split, count in source_counts.items():
        print(f"- {split}: {count}")
    print(f"Output: {TEST_OUT}")
    print(f"Rows: {len(test_rows)}")


if __name__ == "__main__":
    main()
