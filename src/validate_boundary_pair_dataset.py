import argparse
import csv
from collections import Counter
from pathlib import Path


REQUIRED_COLUMNS = ["boundary_pair", "segment_id", "title", "text", "gold_role", "contrast_role", "difficulty", "notes"]
VALID_ROLES = {"BACKGROUND", "CLAIM", "DEFINE", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"}
VALID_DIFFICULTIES = {"EASY", "MEDIUM", "HARD"}
FORBIDDEN_HEADINGS = [
    "### CLAIM",
    "### DEFINE",
    "### METHOD",
    "### RESULT",
    "### LIMITATION",
    "### NEXT_STEP",
    "### EXAMPLE",
    "### BACKGROUND",
]


def roles_for_pair(boundary_pair):
    left, right = boundary_pair.split("_vs_")
    return left, right


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()

    with Path(args.csv).open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    invalid = []
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing:
        invalid.append(f"missing columns: {', '.join(missing)}")
    if len(rows) != 200:
        invalid.append(f"expected 200 rows, got {len(rows)}")

    seen = set()
    boundary_counts = Counter(row.get("boundary_pair", "") for row in rows)
    for boundary_pair, count in boundary_counts.items():
        if count != 25:
            invalid.append(f"{boundary_pair}: expected 25 rows, got {count}")

    for index, row in enumerate(rows, start=2):
        row_errors = []
        segment_id = row.get("segment_id", "")
        if segment_id in seen:
            row_errors.append("duplicate segment_id")
        seen.add(segment_id)
        if not row.get("text", "").strip():
            row_errors.append("empty text")
        if any(heading in row.get("text", "") for heading in FORBIDDEN_HEADINGS):
            row_errors.append("forbidden route heading")
        if row.get("gold_role") not in VALID_ROLES:
            row_errors.append(f"invalid gold_role={row.get('gold_role')}")
        if row.get("contrast_role") not in VALID_ROLES:
            row_errors.append(f"invalid contrast_role={row.get('contrast_role')}")
        if row.get("difficulty") not in VALID_DIFFICULTIES:
            row_errors.append(f"invalid difficulty={row.get('difficulty')}")
        try:
            left, right = roles_for_pair(row.get("boundary_pair", ""))
            if row.get("gold_role") not in {left, right}:
                row_errors.append("gold_role not in boundary_pair")
            expected_contrast = right if row.get("gold_role") == left else left
            if row.get("contrast_role") != expected_contrast:
                row_errors.append("contrast_role is not the other boundary role")
        except ValueError:
            row_errors.append("invalid boundary_pair format")
        if row_errors:
            invalid.append(f"line {index} {segment_id}: {'; '.join(row_errors)}")

    print("Role counts:")
    for role, count in Counter(row.get("gold_role", "") for row in rows).most_common():
        print(f"- {role}: {count}")
    print("Boundary-pair counts:")
    for pair, count in boundary_counts.most_common():
        print(f"- {pair}: {count}")
    print("Difficulty counts:")
    for difficulty, count in Counter(row.get("difficulty", "") for row in rows).most_common():
        print(f"- {difficulty}: {count}")
    print(f"Invalid rows: {len(invalid)}")
    for item in invalid:
        print(f"- {item}")
    print("Validation status: PASS" if not invalid else "Validation status: FAIL")


if __name__ == "__main__":
    main()
