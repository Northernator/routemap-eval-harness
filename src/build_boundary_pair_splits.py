import csv
import random
from collections import Counter, defaultdict
from pathlib import Path


INPUT_PATH = Path("data/v1/gold/boundary_pair_role_eval_v1.csv")
OUTPUTS = {
    "train": Path("data/v1/gold/boundary_pair_train_v1.csv"),
    "dev": Path("data/v1/gold/boundary_pair_dev_v1.csv"),
    "test": Path("data/v1/gold/boundary_pair_test_v1.csv"),
}
SEED = 42


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def split_group(rows, rng):
    shuffled = list(rows)
    rng.shuffle(shuffled)
    n = len(shuffled)
    if n == 13:
        return {"train": shuffled[:8], "dev": shuffled[8:10], "test": shuffled[10:]}
    if n == 12:
        return {"train": shuffled[:7], "dev": shuffled[7:10], "test": shuffled[10:]}
    train_end = round(n * 0.6)
    dev_end = train_end + round(n * 0.2)
    return {"train": shuffled[:train_end], "dev": shuffled[train_end:dev_end], "test": shuffled[dev_end:]}


def main():
    rows = read_rows(INPUT_PATH)
    rng = random.Random(SEED)
    groups = defaultdict(list)
    for row in rows:
        groups[(row["boundary_pair"], row["gold_role"])].append(row)

    splits = {"train": [], "dev": [], "test": []}
    for key in sorted(groups):
        group_splits = split_group(groups[key], rng)
        for split, split_rows in group_splits.items():
            for row in split_rows:
                out = dict(row)
                out["split"] = split
                splits[split].append(out)

    base_fields = list(rows[0].keys())
    fieldnames = ["split"] + base_fields
    for split, path in OUTPUTS.items():
        split_rows = sorted(splits[split], key=lambda row: row["segment_id"])
        with path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(split_rows)

    print("Row counts by split:")
    for split in ["train", "dev", "test"]:
        print(f"- {split}: {len(splits[split])}")
        print("  boundary_pair counts:")
        for pair, count in Counter(row["boundary_pair"] for row in splits[split]).most_common():
            print(f"  - {pair}: {count}")
        print("  gold_role counts:")
        for role, count in Counter(row["gold_role"] for row in splits[split]).most_common():
            print(f"  - {role}: {count}")


if __name__ == "__main__":
    main()
