import csv
import random
from pathlib import Path

import build_heldout_r6_predictions as heldout_builder


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/v1/gold/v1_full_extraction_gold_v1_noleak.csv"
CALIBRATION = ROOT / "data/v1/gold/heldout_full_extraction_gold_v2_adjudicated.csv"
EXPANDED = ROOT / "data/v1/gold/expanded_test_v2.csv"
OUT_ROOT = ROOT / "data/v1/heldout/natural_language_blind"
NATURAL_GOLD = OUT_ROOT / "natural_language_blind_gold.csv"
PROVENANCE = OUT_ROOT / "NATURAL_LANGUAGE_BLIND_PROVENANCE.md"
RUN_ROOT = OUT_ROOT / "r6_generalisation"
PRED_DIR = RUN_ROOT / "predictions"
REPORT_DIR = RUN_ROOT / "reports"
SEED = 20260622

REQUIRED = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
]


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"No rows found in required file: {path}")
    missing = [column for column in REQUIRED if column not in rows[0]]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {', '.join(missing)}")
    return rows


def segment_ids(path):
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return {row["segment_id"] for row in csv.DictReader(source) if row.get("segment_id")}


def create_or_reuse_split():
    if NATURAL_GOLD.exists():
        rows = read_csv(NATURAL_GOLD)
        return rows, "reused_existing"

    source_rows = read_csv(SOURCE)
    excluded = segment_ids(CALIBRATION) | segment_ids(EXPANDED)
    eligible = [row for row in source_rows if row["segment_id"] not in excluded]
    if not eligible:
        raise ValueError("No eligible natural-language rows remained after calibration/EXPAND exclusions")

    rng = random.Random(SEED)
    rows = list(eligible)
    rng.shuffle(rows)

    NATURAL_GOLD.parent.mkdir(parents=True, exist_ok=True)
    with NATURAL_GOLD.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows, "created"


def write_split_provenance(rows, status):
    prefixes = sorted({row["segment_id"].split("_S")[0] for row in rows})
    lines = [
        "# Natural Language Blind Split Provenance",
        "",
        f"- output: `{NATURAL_GOLD.relative_to(ROOT)}`",
        f"- source file: `{SOURCE.relative_to(ROOT)}`",
        f"- split creation status: {status}",
        f"- random seed: {SEED}",
        f"- final row count: {len(rows)}",
        f"- segment ID pattern: {', '.join(prefixes)}",
        "- exclusion rules: removed any segment_id present in HELDOUT2 calibration or EXPAND boundary-stress heldout sets",
        "- true blind status: constructed pseudo-blind split, not a true blind split",
        "- why it qualifies: natural route-note document segments, full-extraction compatible, larger than expanded_test_v2, distinct from HELDOUT2 calibration and EXPAND boundary-stress rows",
        "- limitations: source is historical v1 train/dev-allowed corpus; gold fields are first-pass/locked benchmark labels rather than fresh independent adjudication; this should support promotion confidence but not replace a new externally collected blind set",
        "- gold files modified: no",
    ]
    PROVENANCE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def patch_heldout_builder_paths():
    heldout_builder.SOURCE_SPLIT = NATURAL_GOLD
    heldout_builder.OUT_ROOT = RUN_ROOT
    heldout_builder.PRED_DIR = PRED_DIR
    heldout_builder.REPORT_DIR = REPORT_DIR
    heldout_builder.RAW_OLLAMA_OUT = PRED_DIR / "ollama_llama31_natural_blind_outputs.jsonl"
    heldout_builder.COMBINED_OUT = PRED_DIR / "combined_v3_natural_blind_predictions.csv"
    heldout_builder.D_OUT = PRED_DIR / "D_natural_blind_predictions.csv"
    heldout_builder.R6_OUT = PRED_DIR / "R6_natural_blind_predictions.csv"
    heldout_builder.PROVENANCE_OUT = REPORT_DIR / "NATURAL_BLIND_R6_PREDICTION_PROVENANCE.md"


def write_prediction_provenance(rows):
    path = REPORT_DIR / "NATURAL_BLIND_R6_PREDICTION_PROVENANCE.md"
    lines = [
        "# Natural Blind R6 Prediction Provenance",
        "",
        f"- natural split: `{NATURAL_GOLD.relative_to(ROOT)}`",
        f"- rows: {len(rows)}",
        "- combined_v3: fixed boundary-augmented role model selected before this test; ontology_v1 entities; combined_v3 status/relation/answer rules",
        "- D: Ollama llama3.1 role/status/relation; ontology_v1 entities; combined_v3 answer relevance",
        "- R6: unchanged coarse_3 guard between D/Ollama role and combined_v3 role; ontology_v1 entities; combined_v3 status/relation/answer",
        "- gold labels were not used to generate or alter predictions",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows, status = create_or_reuse_split()
    write_split_provenance(rows, status)
    patch_heldout_builder_paths()
    heldout_builder.main()
    write_split_provenance(rows, status)
    write_prediction_provenance(rows)
    print("natural_blind_r6_prediction_build")
    print(f"natural_gold={NATURAL_GOLD.relative_to(ROOT)}")
    print(f"natural_rows={len(rows)}")
    print(f"split_status={status}")
    print("blind_status=constructed_pseudo_blind")
    print(f"predictions_dir={PRED_DIR.relative_to(ROOT)}")
    print(f"provenance={PROVENANCE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
