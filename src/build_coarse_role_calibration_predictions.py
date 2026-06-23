import csv
from pathlib import Path

from role_taxonomies import map_role


D_PATH = Path("data/v1/hybrid/field_ablation/predictions/D_add_combined_answer_predictions.csv")
COMBINED_PATH = Path("data/v1/gold/heldout_full_extraction_pred_combined_v3_fresh.csv")
OUT_DIR = Path("data/v1/hybrid/coarse_role_calibration/predictions")

D_REQUIRED = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "pred_role",
    "pred_entities",
    "pred_operative_status",
    "pred_relation",
    "pred_answer_relevant",
    "pred_valid",
]

COMBINED_REQUIRED = [
    "segment_id",
    "pred_role_combined_v3",
    "pred_operative_status_combined_v3",
    "pred_relation_combined_v3",
    "pred_answer_relevant_combined_v3",
]

VARIANTS = [
    "R0_D_baseline_copy",
    "R1_combined_role_fallback_on_disagreement",
    "R2_coarse3_guard",
    "R3_coarse4_guard",
    "R4_coarse5_guard",
    "R5_coarse3_guard_combined_relation",
    "R6_coarse3_guard_combined_status_relation",
]


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def require_columns(rows, required, label):
    if not rows:
        raise ValueError(f"{label} has no rows")
    missing = [column for column in required if column not in rows[0]]
    if missing:
        raise ValueError(f"{label} missing columns: {', '.join(missing)}")


def index_by_segment(rows, label):
    indexed = {}
    for row in rows:
        segment_id = row.get("segment_id", "")
        if not segment_id:
            raise ValueError(f"{label} row missing segment_id")
        if segment_id in indexed:
            raise ValueError(f"{label} duplicate segment_id: {segment_id}")
        indexed[segment_id] = row
    return indexed


def role_for_variant(name, d_role, combined_role):
    if name == "R0_D_baseline_copy":
        return d_role
    if name == "R1_combined_role_fallback_on_disagreement":
        return combined_role if d_role != combined_role else d_role
    if name in {"R2_coarse3_guard", "R5_coarse3_guard_combined_relation", "R6_coarse3_guard_combined_status_relation"}:
        return combined_role if map_role(d_role, "coarse_3") != map_role(combined_role, "coarse_3") else d_role
    if name == "R3_coarse4_guard":
        return combined_role if map_role(d_role, "coarse_4") != map_role(combined_role, "coarse_4") else d_role
    if name == "R4_coarse5_guard":
        return combined_role if map_role(d_role, "coarse_5") != map_role(combined_role, "coarse_5") else d_role
    raise KeyError(f"Unknown variant: {name}")


def build_variant(name, d_rows, combined_by_segment):
    output = []
    for d_row in d_rows:
        segment_id = d_row["segment_id"]
        if segment_id not in combined_by_segment:
            raise ValueError(f"combined_v3 missing segment_id: {segment_id}")
        combined = combined_by_segment[segment_id]
        row = dict(d_row)
        row["pred_role"] = role_for_variant(name, d_row["pred_role"], combined["pred_role_combined_v3"])
        if name == "R5_coarse3_guard_combined_relation":
            row["pred_relation"] = combined["pred_relation_combined_v3"]
        if name == "R6_coarse3_guard_combined_status_relation":
            row["pred_operative_status"] = combined["pred_operative_status_combined_v3"]
            row["pred_relation"] = combined["pred_relation_combined_v3"]
        row["pred_provider"] = f"coarse_role_calibration_{name}"
        row["pred_model"] = "ollama_role_with_combined_v3_role_guard"
        row["pred_rationale"] = (
            f"{name}: role calibrated from D/Ollama and combined_v3 predictions; "
            "entities and answer from D; optional status/relation from combined_v3."
        )
        output.append(row)
    return output


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    d_rows = read_rows(D_PATH)
    combined_rows = read_rows(COMBINED_PATH)
    require_columns(d_rows, D_REQUIRED, str(D_PATH))
    require_columns(combined_rows, COMBINED_REQUIRED, str(COMBINED_PATH))
    combined_by_segment = index_by_segment(combined_rows, "combined_v3")

    for name in VARIANTS:
        rows = build_variant(name, d_rows, combined_by_segment)
        out_path = OUT_DIR / f"{name}_predictions.csv"
        write_rows(out_path, rows)
        print(f"{name}: {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
