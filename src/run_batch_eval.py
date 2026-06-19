import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def rel(path):
    return str(Path(path))


def run(args, capture=False):
    command = [sys.executable, *args]
    print("$", " ".join(command), flush=True)
    if capture:
        result = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.stdout
    subprocess.run(command, cwd=ROOT, check=True)
    return ""


def git_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def count_documents(documents):
    root = Path(documents)
    return len(list(root.glob("*.txt")) + list(root.glob("*.md")))


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


def retrieval_summary(run_dir):
    frames = []
    for name in ["baseline_results.csv", "routemap_results.csv", "neural_embedding_results.csv"]:
        path = run_dir / name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "method" not in df.columns or df.empty:
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
    ).sort_values(["Hit@K", "MRR", "comparison reduction %"], ascending=False)


def write_manifest(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_summary(path, retrieval, route_summary, qa_summary, manifest):
    comparison = retrieval[["method", "comparisons/query", "comparison reduction %"]] if not retrieval.empty else pd.DataFrame()
    text = "\n\n".join([
        f"# RouteMap Batch Evaluation Run {manifest['timestamp']}",
        "## Retrieval Comparison\n\n" + markdown_table(retrieval),
        "## Route Extraction Summary\n\n" + markdown_table(route_summary),
        "## QA Judgement Summary\n\n" + markdown_table(qa_summary),
        "## Comparison Reduction Summary\n\n" + markdown_table(comparison),
        "## Known Limitations\n\n"
        "- Demo QA uses small sample labels, not a large human-reviewed corpus.\n"
        "- Stub LLM route extraction copies gold labels when present, so it is a pipeline check, not model evidence.\n"
        "- Deterministic QA judging uses lexical/source proxies rather than human or evaluator-model judgement.\n"
        "- Neural baseline only runs when optional `sentence-transformers` is installed and may download model files.",
    ])
    path.write_text(text + "\n", encoding="utf-8")


def combine_qa_judgements(run_dir, methods):
    score_frames = []
    for method in methods:
        answers = run_dir / f"answers_{method}.csv"
        if not answers.exists():
            continue
        temp_scores = run_dir / f"_qa_judgement_scores_{method}.csv"
        temp_summary = run_dir / f"_qa_judgement_summary_{method}.csv"
        run([
            "src/judge_answers.py",
            "--answers",
            rel(answers),
            "--gold-qa",
            rel(CURRENT_ARGS.gold_qa),
            "--out",
            rel(temp_scores),
            "--summary-out",
            rel(temp_summary),
        ])
        if temp_scores.exists():
            score_frames.append(pd.read_csv(temp_scores))
        temp_scores.unlink(missing_ok=True)
        temp_summary.unlink(missing_ok=True)

    scores = pd.concat(score_frames, ignore_index=True) if score_frames else pd.DataFrame()
    scores.to_csv(run_dir / "qa_judgement_scores.csv", index=False)
    if scores.empty:
        summary = pd.DataFrame()
    else:
        summary = scores.drop(columns=["query_id"]).groupby("method").mean(numeric_only=True).reset_index()
    summary.to_csv(run_dir / "qa_judgement_summary.csv", index=False)
    print("== combined QA judgement summary ==")
    print(summary.to_string(index=False))
    return summary


CURRENT_ARGS = None


def main():
    global CURRENT_ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--documents", required=True)
    ap.add_argument("--gold-segments", required=True)
    ap.add_argument("--gold-qa", required=True)
    ap.add_argument("--out", default="data/runs")
    ap.add_argument("--disable-neural", action="store_true")
    ap.add_argument("--llm-provider", default="stub", choices=["stub", "openai", "anthropic", "ollama"])
    ap.add_argument("--llm-model", default="")
    args = ap.parse_args()
    CURRENT_ARGS = args

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out) / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)

    optional_deps = {
        "sentence_transformers": importlib.util.find_spec("sentence_transformers") is not None,
    }
    neural_enabled = optional_deps["sentence_transformers"] and not args.disable_neural
    methods = ["keyword", "routemap"]

    run([
        "src/run_baselines.py",
        "--gold-segments",
        args.gold_segments,
        "--gold-qa",
        args.gold_qa,
        "--out",
        rel(run_dir / "baseline_results.csv"),
    ])
    run([
        "src/run_routemap.py",
        "--gold-segments",
        args.gold_segments,
        "--gold-qa",
        args.gold_qa,
        "--out",
        rel(run_dir / "routemap_results.csv"),
    ])
    if neural_enabled:
        methods.append("neural")
        run([
            "src/run_neural_embeddings.py",
            "--gold-segments",
            args.gold_segments,
            "--gold-qa",
            args.gold_qa,
            "--out",
            rel(run_dir / "neural_embedding_results.csv"),
        ])

    llm_args = [
        "src/run_llm_route_extractor.py",
        "--segments",
        args.gold_segments,
        "--out",
        rel(run_dir / "llm_route_labels.csv"),
        "--provider",
        args.llm_provider,
        "--errors-out",
        rel(run_dir / "llm_route_errors.csv"),
    ]
    if args.llm_model:
        llm_args.extend(["--model", args.llm_model])
    run(llm_args)
    run([
        "src/score_route_extraction.py",
        "--gold",
        args.gold_segments,
        "--pred",
        rel(run_dir / "llm_route_labels.csv"),
        "--out",
        rel(run_dir / "route_extraction_scores.csv"),
        "--role-confusion-out",
        rel(run_dir / "role_confusion_matrix.csv"),
        "--status-confusion-out",
        rel(run_dir / "status_confusion_matrix.csv"),
        "--relation-confusion-out",
        rel(run_dir / "relation_confusion_matrix.csv"),
    ])

    for method in methods:
        run([
            "src/generate_answers.py",
            "--gold-qa",
            args.gold_qa,
            "--gold-segments",
            args.gold_segments,
            "--method",
            method,
            "--out",
            rel(run_dir / f"answers_{method}.csv"),
        ])

    qa_summary = combine_qa_judgements(run_dir, methods)
    score_stdout = run(["src/score_results.py", "--outputs", rel(run_dir)], capture=True)
    (run_dir / "score_results_summary.txt").write_text(score_stdout, encoding="utf-8")

    gold_segments = pd.read_csv(args.gold_segments, keep_default_na=False)
    gold_qa = pd.read_csv(args.gold_qa, keep_default_na=False)
    manifest = {
        "timestamp": timestamp,
        "git_commit": git_commit(),
        "document_count": count_documents(args.documents),
        "segment_count": int(len(gold_segments)),
        "qa_query_count": int(len(gold_qa)),
        "methods_run": methods,
        "python_version": sys.version,
        "optional_dependencies_detected": optional_deps,
        "neural_disabled": bool(args.disable_neural),
        "run_dir": str(run_dir),
    }
    write_manifest(run_dir / "run_manifest.json", manifest)

    retrieval = retrieval_summary(run_dir)
    route_summary = pd.read_csv(run_dir / "route_extraction_scores.csv")
    write_summary(run_dir / "run_summary.md", retrieval, route_summary, qa_summary, manifest)
    print(f"Batch run complete: {run_dir}")


if __name__ == "__main__":
    main()
