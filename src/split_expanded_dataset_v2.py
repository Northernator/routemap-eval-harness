import csv
import random
from collections import Counter, defaultdict
from pathlib import Path


INPUT = Path("data/v1/gold/expanded_boundary_entity_dataset_v2.csv")
OUTS = {
    "train": Path("data/v1/gold/expanded_train_v2.csv"),
    "dev": Path("data/v1/gold/expanded_dev_v2.csv"),
    "test": Path("data/v1/gold/expanded_test_v2.csv"),
}


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def key_for(row):
    return (row.get("dataset_family", ""), row.get("boundary_pair", ""), row.get("gold_role", ""))


def split_group(rows, group_key):
    shuffled = list(rows)
    random.Random(42 + len(rows)).shuffle(shuffled)
    n = len(shuffled)
    if group_key[0] == "boundary_pair" and n == 25:
        train_n = 18
        dev_n = 4
    elif group_key[0] == "entity_focus" and n == 20:
        train_n = 13
        dev_n = 3 if group_key[2] in {"BACKGROUND", "CLAIM", "DEFINE", "METHOD"} else 2
    else:
        train_n = round(n * 0.70)
        dev_n = round(n * 0.15)
    return {
        "train": shuffled[:train_n],
        "dev": shuffled[train_n:train_n + dev_n],
        "test": shuffled[train_n + dev_n:],
    }


def main():
    rows = read_rows(INPUT)
    groups = defaultdict(list)
    for row in rows:
        groups[key_for(row)].append(row)
    splits = {"train": [], "dev": [], "test": []}
    for group_key, group_rows in groups.items():
        for split, items in split_group(group_rows, group_key).items():
            for item in items:
                out = dict(item)
                out["split"] = f"expanded_{split}_v2"
                splits[split].append(out)

    fieldnames = ["split"] + list(rows[0].keys())
    for split, path in OUTS.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sorted(splits[split], key=lambda row: row["segment_id"]))

    for split, items in splits.items():
        print(f"{split}: {len(items)}")
        print("  gold roles:", dict(Counter(row["gold_role"] for row in items)))
        print("  families:", dict(Counter(row["dataset_family"] for row in items)))
        print("  boundary pairs:", dict(Counter(row["boundary_pair"] for row in items).most_common(10)))


if __name__ == "__main__":
    main()
