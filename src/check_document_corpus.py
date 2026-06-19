import argparse
from collections import Counter
from pathlib import Path
import pandas as pd
from common import read_text, split_segments


ROLE_HINTS = {
    "define_definition": ["define", "defined", "definition", "refers to", "means"],
    "method": ["method", "compute", "computed", "procedure", "algorithm"],
    "result": ["result", "shows", "finding", "reported", "observed"],
    "limitation": ["limitation", "caveat", "constraint", "weakness", "uncertain"],
    "next_step": ["next step", "future work", "follow up", "planned", "todo"],
    "example": ["example", "for example", "illustration", "illustrative"],
}


def document_paths(root):
    root = Path(root)
    return sorted(list(root.glob("*.txt")) + list(root.glob("*.md")))


def hint_counts(text):
    lowered = text.lower()
    return {
        name: sum(lowered.count(token) for token in tokens)
        for name, tokens in ROLE_HINTS.items()
    }


def build_rows(paths):
    rows = []
    for path in paths:
        text = read_text(path)
        segments = split_segments(text)
        row = {
            "file_name": path.name,
            "path": str(path),
            "extension": path.suffix.lower(),
            "characters": len(text),
            "estimated_segments": len(segments),
            "too_little_text": len(text.strip()) < 500,
        }
        row.update(hint_counts(text))
        rows.append(row)
    return rows


def markdown_report(rows, docs_path):
    df = pd.DataFrame(rows)
    lines = [f"# Corpus Report: {docs_path}", ""]
    if df.empty:
        lines.extend([
            "Document count: 0",
            "",
            "No `.txt` or `.md` documents found. Add source documents before annotation.",
        ])
        return "\n".join(lines) + "\n"

    duplicate_names = sorted([name for name, count in Counter(df.file_name).items() if count > 1])
    shortest = df.sort_values("characters").iloc[0]
    longest = df.sort_values("characters", ascending=False).iloc[0]
    too_short = df[df.too_little_text]
    type_counts = df.extension.value_counts().sort_index()

    file_type_summary = ", ".join(f"{ext or '[none]'}={count}" for ext, count in type_counts.items())
    lines.extend([
        f"Document count: {len(df)}",
        f"File types: {file_type_summary}",
        f"Total characters: {int(df.characters.sum())}",
        f"Estimated segment count: {int(df.estimated_segments.sum())}",
        f"Shortest document: {shortest.file_name} ({int(shortest.characters)} chars)",
        f"Longest document: {longest.file_name} ({int(longest.characters)} chars)",
        "",
        "Files with too little text:",
    ])
    if too_short.empty:
        lines.append("- none")
    else:
        for _, row in too_short.iterrows():
            lines.append(f"- {row.file_name}: {int(row.characters)} chars")

    lines.append("")
    lines.append("Duplicate file names:")
    if duplicate_names:
        lines.extend(f"- {name}" for name in duplicate_names)
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Role keyword hints:")
    for name in ROLE_HINTS:
        lines.append(f"- {name}: {int(df[name].sum())}")

    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="data/v1/documents")
    ap.add_argument("--out-md", default="")
    ap.add_argument("--out-csv", default="")
    args = ap.parse_args()

    docs_path = Path(args.docs)
    base = docs_path.parent if docs_path.name == "documents" else docs_path
    out_md = Path(args.out_md) if args.out_md else base / "corpus_report.md"
    out_csv = Path(args.out_csv) if args.out_csv else base / "corpus_report.csv"

    rows = build_rows(document_paths(docs_path))
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    report = markdown_report(rows, docs_path)
    out_md.write_text(report, encoding="utf-8")
    print(report, end="")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_csv}")


if __name__ == "__main__":
    main()
