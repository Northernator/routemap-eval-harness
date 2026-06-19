import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V1_ROOT = ROOT / "data" / "v1"
V1_DOCUMENTS = V1_ROOT / "documents"
V1_GOLD = V1_ROOT / "gold"
V1_RUNS = V1_ROOT / "runs"


TEMPLATE_FILES = [
    "ANNOTATION_GUIDELINES.md",
    "gold_segments_template.csv",
    "gold_qa_template.csv",
    "annotation_batch.csv",
    "v1_annotation_targets.csv",
    "v1_qa_targets.csv",
]


def copy_templates():
    source = ROOT / "data" / "gold"
    for name in TEMPLATE_FILES:
        src = source / name
        if src.exists():
            shutil.copy2(src, V1_GOLD / name)


def write_workspace_readme():
    text = """# RouteMap v1.0 Benchmark Workspace

Place benchmark source documents in:

```text
data/v1/documents/
```

Human-gold annotation and QA files live in:

```text
data/v1/gold/
```

Timestamped benchmark runs are written to:

```text
data/v1/runs/
```

Start with the root checklist:

```text
docs/V1_RUN_CHECKLIST.md
```
"""
    (V1_ROOT / "README.md").write_text(text, encoding="utf-8")


def print_next_commands():
    print("v1 benchmark workspace ready.")
    print()
    print("Place .txt or .md benchmark documents in data/v1/documents/")
    print()
    print("Next commands from docs/V1_RUN_CHECKLIST.md, adjusted for data/v1 paths:")
    print()
    commands = [
        "python src/build_annotation_batch.py --docs data/v1/documents --out data/v1/gold/annotation_batch.csv",
        "python src/sample_annotation_targets.py --gold data/v1/gold/annotation_batch.csv --out data/v1/gold/v1_annotation_targets.csv --max-per-role 50",
        "copy data\\v1\\gold\\v1_annotation_targets.csv data\\v1\\gold\\v1_annotation_targets_filled.csv",
        "python src/validate_gold_labels.py --gold data/v1/gold/v1_annotation_targets_filled.csv --summary",
        "python src/build_qa_targets.py --gold-segments data/v1/gold/v1_annotation_targets_filled.csv --out data/v1/gold/v1_qa_targets.csv",
        "copy data\\v1\\gold\\v1_qa_targets.csv data\\v1\\gold\\v1_qa_targets_filled.csv",
        "python src/validate_qa_targets.py --qa data/v1/gold/v1_qa_targets_filled.csv --gold-segments data/v1/gold/v1_annotation_targets_filled.csv",
        "python src/run_batch_eval.py --documents data/v1/documents --gold-segments data/v1/gold/v1_annotation_targets_filled.csv --gold-qa data/v1/gold/v1_qa_targets_filled.csv --out data/v1/runs",
        "python src/generate_run_report.py --run-dir data/v1/runs/<timestamp>",
    ]
    for command in commands:
        print(command)


def main():
    V1_DOCUMENTS.mkdir(parents=True, exist_ok=True)
    V1_GOLD.mkdir(parents=True, exist_ok=True)
    V1_RUNS.mkdir(parents=True, exist_ok=True)
    copy_templates()
    write_workspace_readme()
    print_next_commands()


if __name__ == "__main__":
    main()
