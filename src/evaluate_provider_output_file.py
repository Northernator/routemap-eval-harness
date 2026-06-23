import argparse
import subprocess
import sys
from pathlib import Path


REQUESTS = "data/v1/llm_eval/requests/fresh_adjudicated_requests.jsonl"
GOLD = "data/v1/gold/model_test_fresh_adjudicated_role.csv"
REPORTS = Path("data/v1/llm_eval/reports")
PREDICTIONS = Path("data/v1/llm_eval/predictions")


def run(command):
    print(" ".join(command))
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-output", required=True)
    parser.add_argument("--provider-name", required=True)
    args = parser.parse_args()

    validation = REPORTS / f"{args.provider_name}_validation.md"
    predictions = PREDICTIONS / f"{args.provider_name}_predictions.csv"
    evaluation = REPORTS / f"{args.provider_name}_evaluation.md"
    rows = REPORTS / f"{args.provider_name}_evaluation_rows.csv"
    comparison = REPORTS / "LLM_PROVIDER_COMPARISON.md"

    run([sys.executable, "src/validate_llm_extraction_outputs.py", "--requests", REQUESTS, "--outputs", args.provider_output, "--report", str(validation)])
    run([sys.executable, "src/ingest_llm_extraction_outputs.py", "--gold", GOLD, "--outputs", args.provider_output, "--out", str(predictions), "--provider-name", args.provider_name])
    run([sys.executable, "src/evaluate_llm_extraction_predictions.py", "--csv", str(predictions), "--out-md", str(evaluation), "--out-csv", str(rows)])
    run([sys.executable, "src/compare_llm_provider_runs.py", "--reports-dir", str(REPORTS), "--out", str(comparison)])
    print(f"Validation: {validation}")
    print(f"Predictions: {predictions}")
    print(f"Evaluation: {evaluation}")
    print(f"Rows: {rows}")
    print(f"Comparison: {comparison}")


if __name__ == "__main__":
    main()
