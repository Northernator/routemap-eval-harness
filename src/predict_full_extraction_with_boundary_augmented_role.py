import csv
from pathlib import Path


FULL_PRED_PATH = Path("data/v1/gold/heldout_full_extraction_pred_v2_fresh_adjudicated.csv")
ROLE_PRED_PATH = Path("data/v1/gold/boundary_augmented_role_predictions_fresh.csv")
ROLE_RESULTS_PATH = Path("data/v1/gold/boundary_augmented_role_results_fresh.csv")
OUT_PATH = Path("data/v1/gold/heldout_full_extraction_pred_boundary_augmented_role_fresh.csv")

RELATION_BY_ROLE = {
    "BACKGROUND": "sets_context",
    "DEFINE": "defines",
    "CLAIM": "asserts",
    "METHOD": "recommends",
    "RESULT": "reports_usefulness",
    "LIMITATION": "limits",
    "NEXT_STEP": "proposes_next_test",
    "EXAMPLE": "gives_example",
}


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def prediction_column(setting, model):
    return f"pred_{setting}_{model}"


def select_best_prediction_column():
    rows = read_rows(ROLE_RESULTS_PATH)
    overall = [row for row in rows if row.get("metric_type") == "overall"]
    if not overall:
        raise ValueError(f"No overall rows found in {ROLE_RESULTS_PATH}")
    best = max(overall, key=lambda row: float(row["accuracy"]))
    column = prediction_column(best["setting"], best["model"])
    return column, best


def main():
    best_column, best_row = select_best_prediction_column()
    full_rows = read_rows(FULL_PRED_PATH)
    role_rows = read_rows(ROLE_PRED_PATH)
    by_segment = {row["segment_id"]: row for row in role_rows}

    if not full_rows:
        raise ValueError(f"No rows found in {FULL_PRED_PATH}")
    fieldnames = list(full_rows[0].keys())
    for column in ["pred_role_boundary_augmented", "pred_relation_boundary_augmented"]:
        if column not in fieldnames:
            fieldnames.append(column)

    merged = []
    for row in full_rows:
        segment_id = row["segment_id"]
        role_row = by_segment.get(segment_id)
        role = role_row.get(best_column, "") if role_row is not None else ""
        out = dict(row)
        out["pred_role_boundary_augmented"] = role
        out["pred_relation_boundary_augmented"] = RELATION_BY_ROLE.get(role, "")
        merged.append(out)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)

    excluded = sum(1 for row in merged if row.get("include_in_eval") == "NO")
    print(f"Selected setting: {best_row['setting']}")
    print(f"Selected model: {best_row['model']}")
    print(f"Selected prediction column: {best_column}")
    print(f"Selected role accuracy: {float(best_row['accuracy']):.3f}")
    print(f"Rows written: {len(merged)}")
    print(f"Excluded rows: {excluded}")
    print(f"Output: {OUT_PATH}")


if __name__ == "__main__":
    main()
