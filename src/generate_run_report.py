import argparse
import html
import json
from pathlib import Path
import pandas as pd


def load_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib is required for reports. Install with: python -m pip install matplotlib") from exc
    return plt


def read_csv(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, keep_default_na=False)


def retrieval_summary(run_dir):
    frames = []
    for name in ["baseline_results.csv", "routemap_results.csv", "neural_embedding_results.csv"]:
        df = read_csv(run_dir / name)
        if df.empty or "method" not in df.columns:
            continue
        if "comparison_reduction_pct" not in df.columns:
            df["comparison_reduction_pct"] = 0.0
        frames.append(df[["method", "hit", "mrr", "comparisons", "comparison_reduction_pct"]])
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    return combined.groupby("method", as_index=False).agg(
        **{
            "Hit@K": ("hit", "mean"),
            "MRR": ("mrr", "mean"),
            "comparisons/query": ("comparisons", "mean"),
            "comparison reduction %": ("comparison_reduction_pct", "mean"),
        }
    )


def markdown_table(df):
    if df.empty:
        return "_No rows._"
    table = df.fillna("").astype(str)
    columns = list(table.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in table.iterrows():
        lines.append("| " + " | ".join(row[column] for column in columns) + " |")
    return "\n".join(lines)


def html_table(df):
    if df.empty:
        return "<p><em>No rows.</em></p>"
    return df.to_html(index=False, escape=True, border=0, classes="data-table")


def save_grouped_bar(plt, df, x_column, value_columns, path, title, ylabel):
    fig, ax = plt.subplots(figsize=(9, 5))
    if df.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
    else:
        plot_df = df.set_index(x_column)[value_columns].astype(float)
        plot_df.plot(kind="bar", ax=ax)
        ax.set_title(title)
        ax.set_xlabel("")
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
        ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_single_bar(plt, df, x_column, value_column, path, title, ylabel):
    fig, ax = plt.subplots(figsize=(9, 5))
    if df.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
    else:
        ax.bar(df[x_column].astype(str), df[value_column].astype(float))
        ax.set_title(title)
        ax.set_xlabel("")
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_report_md(path, manifest, retrieval, route_scores, qa_summary):
    lines = [
        f"# RouteMap Evaluation Report {manifest.get('timestamp', '')}",
        "",
        "## Run Manifest",
        "",
        f"- Git commit: `{manifest.get('git_commit', '')}`",
        f"- Documents: {manifest.get('document_count', '')}",
        f"- Segments: {manifest.get('segment_count', '')}",
        f"- QA queries: {manifest.get('qa_query_count', '')}",
        f"- Methods: {', '.join(manifest.get('methods_run', []))}",
        "",
        "## Retrieval Comparison",
        "",
        "![Retrieval comparison](charts/retrieval_comparison.png)",
        "",
        markdown_table(retrieval),
        "",
        "## Comparison Reduction",
        "",
        "![Comparison reduction](charts/comparison_reduction.png)",
        "",
        "## Route Extraction Scores",
        "",
        "![Route extraction scores](charts/route_extraction_scores.png)",
        "",
        markdown_table(route_scores),
        "",
        "## QA Judgement",
        "",
        "![QA judgement](charts/qa_judgement.png)",
        "",
        markdown_table(qa_summary),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report_html(path, manifest, retrieval, route_scores, qa_summary):
    title = f"RouteMap Evaluation Report {html.escape(str(manifest.get('timestamp', '')))}"
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; line-height: 1.45; }}
    h1, h2 {{ color: #111827; }}
    img {{ max-width: 920px; width: 100%; display: block; margin: 12px 0 28px; border: 1px solid #e5e7eb; }}
    .data-table {{ border-collapse: collapse; margin: 12px 0 28px; min-width: 640px; }}
    .data-table th, .data-table td {{ border: 1px solid #d1d5db; padding: 6px 10px; text-align: left; }}
    .data-table th {{ background: #f3f4f6; }}
    code {{ background: #f3f4f6; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <h2>Run Manifest</h2>
  <ul>
    <li>Git commit: <code>{html.escape(str(manifest.get('git_commit', '')))}</code></li>
    <li>Documents: {html.escape(str(manifest.get('document_count', '')))}</li>
    <li>Segments: {html.escape(str(manifest.get('segment_count', '')))}</li>
    <li>QA queries: {html.escape(str(manifest.get('qa_query_count', '')))}</li>
    <li>Methods: {html.escape(', '.join(manifest.get('methods_run', [])))}</li>
  </ul>
  <h2>Retrieval Comparison</h2>
  <img src="charts/retrieval_comparison.png" alt="Retrieval comparison chart">
  {html_table(retrieval)}
  <h2>Comparison Reduction</h2>
  <img src="charts/comparison_reduction.png" alt="Comparison reduction chart">
  <h2>Route Extraction Scores</h2>
  <img src="charts/route_extraction_scores.png" alt="Route extraction score chart">
  {html_table(route_scores)}
  <h2>QA Judgement</h2>
  <img src="charts/qa_judgement.png" alt="QA judgement chart">
  {html_table(qa_summary)}
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    charts_dir = run_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    retrieval = retrieval_summary(run_dir)
    route_scores = read_csv(run_dir / "route_extraction_scores.csv")
    qa_summary = read_csv(run_dir / "qa_judgement_summary.csv")

    plt = load_matplotlib()
    save_grouped_bar(
        plt,
        retrieval,
        "method",
        ["Hit@K", "MRR", "comparisons/query"],
        charts_dir / "retrieval_comparison.png",
        "Retrieval Metrics by Method",
        "score / count",
    )
    save_single_bar(
        plt,
        retrieval,
        "method",
        "comparison reduction %",
        charts_dir / "comparison_reduction.png",
        "Comparison Reduction by Method",
        "reduction %",
    )
    route_plot = route_scores[route_scores["metric"].isin([
        "role_accuracy",
        "operative_status_accuracy",
        "relation_accuracy",
        "entity_exact_match",
        "entity_jaccard",
    ])] if not route_scores.empty else pd.DataFrame()
    save_single_bar(
        plt,
        route_plot,
        "metric",
        "value",
        charts_dir / "route_extraction_scores.png",
        "Route Extraction Scores",
        "score",
    )
    qa_columns = ["source_hit", "correctness_proxy", "completeness_proxy"]
    present_qa_columns = [column for column in qa_columns if column in qa_summary.columns]
    save_grouped_bar(
        plt,
        qa_summary,
        "method",
        present_qa_columns,
        charts_dir / "qa_judgement.png",
        "QA Judgement by Method",
        "score",
    )

    write_report_md(run_dir / "report.md", manifest, retrieval, route_scores, qa_summary)
    write_report_html(run_dir / "report.html", manifest, retrieval, route_scores, qa_summary)
    print(f"Wrote {run_dir / 'report.md'}")
    print(f"Wrote {run_dir / 'report.html'}")
    print(f"Wrote charts to {charts_dir}")


if __name__ == "__main__":
    main()
