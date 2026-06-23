import csv
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import split_entity_set
from role_taxonomies import map_role


COMBINED_PATH = Path("data/v1/gold/heldout_full_extraction_pred_combined_v3_fresh.csv")
D_PATH = Path("data/v1/hybrid/field_ablation/predictions/D_add_combined_answer_predictions.csv")
PRED_DIR = Path("data/v1/hybrid/coarse_role_calibration/predictions")
REPORT_DIR = Path("data/v1/hybrid/coarse_role_calibration/reports")
OUT_MD = REPORT_DIR / "COARSE_ROLE_CALIBRATION_COMPARISON.md"
OUT_CSV = REPORT_DIR / "coarse_role_calibration_comparison.csv"

VARIANTS = [
    "R0_D_baseline_copy",
    "R1_combined_role_fallback_on_disagreement",
    "R2_coarse3_guard",
    "R3_coarse4_guard",
    "R4_coarse5_guard",
    "R5_coarse3_guard_combined_relation",
    "R6_coarse3_guard_combined_status_relation",
]

METRICS = [
    "role_accuracy",
    "coarse_5",
    "coarse_4",
    "coarse_3",
    "entity_jaccard",
    "status",
    "relation",
    "answer",
    "strict",
    "relaxed_1",
    "relaxed_2",
    "relaxed_3",
]


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(num, den):
    return num / den if den else 0.0


def entity_jaccard(gold_value, pred_value):
    gold = split_entity_set(gold_value)
    pred = split_entity_set(pred_value)
    return safe_div(len(gold & pred), len(gold | pred))


def evaluate_rows(rows):
    counts = Counter()
    n = 0
    for row in rows:
        n += 1
        entity_j = entity_jaccard(row["gold_entities"], row["pred_entities"])
        role_ok = row["gold_role"] == row["pred_role"]
        coarse5_ok = map_role(row["gold_role"], "coarse_5") == map_role(row["pred_role"], "coarse_5")
        coarse4_ok = map_role(row["gold_role"], "coarse_4") == map_role(row["pred_role"], "coarse_4")
        coarse3_ok = map_role(row["gold_role"], "coarse_3") == map_role(row["pred_role"], "coarse_3")
        status_ok = row["gold_operative_status"] == row["pred_operative_status"]
        relation_ok = row["gold_relation"] == row["pred_relation"]
        answer_ok = row["gold_answer_relevant"] == row["pred_answer_relevant"]
        entity_exact = split_entity_set(row["gold_entities"]) == split_entity_set(row["pred_entities"])
        strict = role_ok and status_ok and relation_ok and answer_ok and entity_exact
        relaxed_1 = role_ok and answer_ok and entity_j >= 0.5
        relaxed_2 = coarse4_ok and answer_ok and entity_j >= 0.5
        relaxed_3 = coarse3_ok and answer_ok and entity_j >= 0.5
        for key, ok in [
            ("role_accuracy", role_ok),
            ("coarse_5", coarse5_ok),
            ("coarse_4", coarse4_ok),
            ("coarse_3", coarse3_ok),
            ("status", status_ok),
            ("relation", relation_ok),
            ("answer", answer_ok),
            ("strict", strict),
            ("relaxed_1", relaxed_1),
            ("relaxed_2", relaxed_2),
            ("relaxed_3", relaxed_3),
        ]:
            counts[key] += int(ok)
        counts["entity_jaccard"] += entity_j
    return {metric: safe_div(counts[metric], n) for metric in METRICS}


def combined_as_standard_rows():
    rows = []
    for row in read_rows(COMBINED_PATH):
        if row.get("include_in_eval", "YES") != "YES":
            continue
        rows.append({
            "gold_role": row["gold_role"],
            "gold_entities": row["gold_entities"],
            "gold_operative_status": row["gold_operative_status"],
            "gold_relation": row["gold_relation"],
            "gold_answer_relevant": row["gold_answer_relevant"],
            "pred_role": row["pred_role_combined_v3"],
            "pred_entities": row["pred_entities_combined_v3"],
            "pred_operative_status": row["pred_operative_status_combined_v3"],
            "pred_relation": row["pred_relation_combined_v3"],
            "pred_answer_relevant": row["pred_answer_relevant_combined_v3"],
        })
    return rows


def standard_prediction_rows(path):
    rows = []
    for row in read_rows(path):
        if row.get("pred_valid") != "YES":
            continue
        rows.append(row)
    return rows


def collect_results():
    results = [{"variant": "combined_v3", **evaluate_rows(combined_as_standard_rows())}]
    results.append({"variant": "D_add_combined_answer", **evaluate_rows(standard_prediction_rows(D_PATH))})
    for variant in VARIANTS:
        path = PRED_DIR / f"{variant}_predictions.csv"
        results.append({"variant": variant, **evaluate_rows(standard_prediction_rows(path))})
    return results


def fmt(value):
    return f"{value:.3f}"


def write_csv(rows):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["variant", *METRICS])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows):
    best_relaxed1 = max(rows, key=lambda row: row["relaxed_1"])
    best_relaxed2 = max(rows, key=lambda row: row["relaxed_2"])
    best_relaxed3 = max(rows, key=lambda row: row["relaxed_3"])
    best_strict_value = max(row["strict"] for row in rows)
    best_strict = [row["variant"] for row in rows if row["strict"] == best_strict_value]
    lines = [
        "# Coarse Role Calibration Comparison",
        "",
        "## Metrics",
        "",
        "| variant | role | coarse_5 | coarse_4 | coarse_3 | entity_jaccard | status | relation | answer | strict | relaxed_1 | relaxed_2 | relaxed_3 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['variant']} | "
            + " | ".join(fmt(row[metric]) for metric in METRICS)
            + " |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        f"Best strict: {', '.join(best_strict)} = {fmt(best_strict_value)}.",
        f"Best relaxed_1: {best_relaxed1['variant']} = {fmt(best_relaxed1['relaxed_1'])}.",
        f"Best relaxed_2: {best_relaxed2['variant']} = {fmt(best_relaxed2['relaxed_2'])}.",
        f"Best relaxed_3: {best_relaxed3['variant']} = {fmt(best_relaxed3['relaxed_3'])}.",
        "",
        "Exact disagreement fallback does not preserve D's relaxed_1 gain. Coarse_3 guarding preserves and improves it while recovering combined_v3's relaxed_3 score.",
        "The coarse_3 guard beats both D and combined_v3 on relaxed_1 and relaxed_2, and ties combined_v3 on relaxed_3.",
        "Among role guards, coarse_3 is the best relaxed_1/2/3 compromise. Coarse_4 and coarse_5 recover coarse scores but lose more fine-role gain.",
        "Adding combined_v3 relation improves relation accuracy but does not improve strict because exact entity match and other field interactions still block rows.",
        "Adding combined_v3 status plus relation improves status but not strict beyond relation alone in this run.",
        "Best current RouteMap v2 candidate from this test is R6_coarse3_guard_combined_status_relation for full extraction: it keeps R2's relaxed balance and recovers strict accuracy to the combined_v3 level. R2 remains the cleanest role-only calibration.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_table(rows):
    print(",".join(["variant", *METRICS]))
    for row in rows:
        print(",".join([row["variant"], *[fmt(row[metric]) for metric in METRICS]]))
    print(f"comparison_md={OUT_MD}")
    print(f"comparison_csv={OUT_CSV}")


def main():
    rows = collect_results()
    write_csv(rows)
    write_markdown(rows)
    print_table(rows)


if __name__ == "__main__":
    main()
