import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(args):
    print("\n$", " ".join([sys.executable, *args]), flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main():
    (ROOT / "data" / "outputs").mkdir(parents=True, exist_ok=True)

    run([
        "src/build_gold_sample.py",
        "--docs",
        "data/documents",
        "--out",
        "data/outputs/gold_segments_sample.csv",
    ])
    run([
        "src/run_baselines.py",
        "--gold-segments",
        "data/gold/gold_segments_filled.csv",
        "--gold-qa",
        "data/gold/gold_qa_filled.csv",
        "--out",
        "data/outputs/baseline_results.csv",
    ])
    run([
        "src/run_routemap.py",
        "--gold-segments",
        "data/gold/gold_segments_filled.csv",
        "--gold-qa",
        "data/gold/gold_qa_filled.csv",
        "--out",
        "data/outputs/routemap_results.csv",
    ])
    run([
        "src/run_llm_route_extractor.py",
        "--segments",
        "data/gold/annotation_batch_filled.csv",
        "--out",
        "data/outputs/llm_route_labels_offline_stub.csv",
    ])
    run([
        "src/score_route_extraction.py",
        "--gold",
        "data/gold/annotation_batch_filled.csv",
        "--pred",
        "data/outputs/llm_route_labels_offline_stub.csv",
        "--out",
        "data/outputs/route_extraction_scores.csv",
    ])
    run([
        "src/generate_answers.py",
        "--gold-qa",
        "data/gold/gold_qa_filled.csv",
        "--gold-segments",
        "data/gold/gold_segments_filled.csv",
        "--method",
        "routemap",
        "--out",
        "data/outputs/answers_routemap.csv",
    ])
    run([
        "src/judge_answers.py",
        "--answers",
        "data/outputs/answers_routemap.csv",
        "--gold-qa",
        "data/gold/gold_qa_filled.csv",
        "--out",
        "data/outputs/qa_judgement_scores.csv",
    ])
    run(["src/score_results.py", "--outputs", "data/outputs"])

    print("\nDemo complete. Outputs are in data/outputs.")


if __name__ == "__main__":
    main()
