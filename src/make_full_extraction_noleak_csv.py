import argparse
import csv
from pathlib import Path


LEADING_HEADINGS = [
    "### BACKGROUND",
    "### CLAIM",
    "### DEFINE",
    "### METHOD",
    "### RESULT",
    "### LIMITATION",
    "### NEXT_STEP",
    "### EXAMPLE",
]


def strip_leading_route_heading(text):
    if text is None:
        return "", False

    for heading in LEADING_HEADINGS:
        if text.startswith(heading):
            return text[len(heading):].lstrip(), True

    return text, False


def make_noleak_csv(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    stripped_count = 0
    for row in rows:
        stripped_text, stripped = strip_leading_route_heading(row.get("text", ""))
        row["text"] = stripped_text
        if stripped:
            stripped_count += 1

    with output_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows), stripped_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input_csv", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    row_count, stripped_count = make_noleak_csv(args.input_csv, args.out)
    print(f"Rows written: {row_count}")
    print(f"Headings stripped: {stripped_count}")
    print(f"Output path: {args.out}")


if __name__ == "__main__":
    main()
