import argparse
import re
from pathlib import Path


BASELINES = [
    ("best local fine_8 role", "0.532"),
    ("ontology_v1 entity Jaccard", "0.506"),
    ("combined_v3 strict", "0.051"),
    ("combined_v3 relaxed_1", "0.253"),
    ("combined_v3 relaxed_2", "0.354"),
    ("combined_v3 relaxed_3", "0.443"),
]


def parse_report(path):
    text = path.read_text(encoding="utf-8")
    metrics = {}
    for line in text.splitlines():
        match = re.match(r"\| ([^|]+) \| ([0-9.]+) \|", line.strip())
        if match:
            metrics[match.group(1).strip()] = match.group(2).strip()
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    eval_reports = sorted(path for path in reports_dir.glob("*evaluation.md") if path.name != "LLM_PROVIDER_COMPARISON.md")
    lines = [
        "# LLM Provider Comparison",
        "",
        "## Local Baselines",
        "",
        "| baseline | score |",
        "|---|---:|",
    ]
    for name, score in BASELINES:
        lines.append(f"| {name} | {score} |")
    lines.extend(["", "## Provider Runs", ""])
    if not eval_reports:
        lines.append("No provider evaluation reports found yet. Run the sample pipeline or add provider outputs first.")
    else:
        lines.extend(["| report | role accuracy | entity Jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 |", "|---|---:|---:|---:|---:|---:|---:|"])
        for path in eval_reports:
            metrics = parse_report(path)
            lines.append(
                f"| {path.name} | {metrics.get('role accuracy', '')} | {metrics.get('entity average Jaccard', '')} | "
                f"{metrics.get('strict full-row accuracy', '')} | {metrics.get('relaxed_1', '')} | "
                f"{metrics.get('relaxed_2', '')} | {metrics.get('relaxed_3', '')} |"
            )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Reports scanned: {len(eval_reports)}")
    print(f"Output: {out}")


if __name__ == "__main__":
    main()
