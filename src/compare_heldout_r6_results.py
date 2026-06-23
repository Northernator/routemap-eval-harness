import csv
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import split_entity_set
from role_taxonomies import map_role


ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = ROOT / "data/v1/heldout/r6_generalisation/predictions"
REPORT_DIR = ROOT / "data/v1/heldout/r6_generalisation/reports"
OUT_MD = REPORT_DIR / "HELDOUT_R6_COMPARISON.md"
OUT_CSV = REPORT_DIR / "heldout_r6_comparison.csv"

VARIANTS = [
    ("combined_v3", PRED_DIR / "combined_v3_heldout_predictions.csv"),
    ("D_add_combined_answer", PRED_DIR / "D_heldout_predictions.csv"),
    ("R6", PRED_DIR / "R6_heldout_predictions.csv"),
]

METRICS = [
    "evaluated_rows",
    "missing_invalid_rows",
    "role",
    "coarse_5",
    "coarse_4",
    "coarse_3",
    "entity_jaccard",
    "entity_exact",
    "status",
    "relation",
    "answer",
    "strict",
    "relaxed_1",
    "relaxed_2",
    "relaxed_3",
]

REQUIRED = [
    "segment_id",
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

CALIBRATION_TARGETS = {
    "combined_v3": {
        "role": 0.532,
        "coarse_3": 0.823,
        "strict": 0.051,
        "relaxed_1": 0.253,
        "relaxed_2": 0.354,
        "relaxed_3": 0.443,
    },
    "R6": {
        "role": 0.709,
        "coarse_3": 0.823,
        "strict": 0.051,
        "relaxed_1": 0.354,
        "relaxed_2": 0.392,
        "relaxed_3": 0.443,
    },
}


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required predictions file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"No rows found in required predictions file: {path}")
    missing = [column for column in REQUIRED if column not in rows[0]]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {', '.join(missing)}")
    return rows


def safe_div(num, den):
    return num / den if den else 0.0


def entity_metrics(gold_value, pred_value):
    gold = split_entity_set(gold_value)
    pred = split_entity_set(pred_value)
    inter = gold & pred
    union = gold | pred
    return gold == pred, safe_div(len(inter), len(union))


def evaluate(rows):
    valid_rows = [row for row in rows if row.get("pred_valid") == "YES"]
    counts = Counter()
    for row in valid_rows:
        entity_exact, entity_j = entity_metrics(row["gold_entities"], row["pred_entities"])
        role_ok = row["gold_role"] == row["pred_role"]
        coarse5_ok = map_role(row["gold_role"], "coarse_5") == map_role(row["pred_role"], "coarse_5")
        coarse4_ok = map_role(row["gold_role"], "coarse_4") == map_role(row["pred_role"], "coarse_4")
        coarse3_ok = map_role(row["gold_role"], "coarse_3") == map_role(row["pred_role"], "coarse_3")
        status_ok = row["gold_operative_status"] == row["pred_operative_status"]
        relation_ok = row["gold_relation"] == row["pred_relation"]
        answer_ok = row["gold_answer_relevant"] == row["pred_answer_relevant"]
        strict = role_ok and status_ok and relation_ok and answer_ok and entity_exact
        relaxed_1 = role_ok and answer_ok and entity_j >= 0.5
        relaxed_2 = coarse4_ok and answer_ok and entity_j >= 0.5
        relaxed_3 = coarse3_ok and answer_ok and entity_j >= 0.5
        for key, ok in [
            ("role", role_ok),
            ("coarse_5", coarse5_ok),
            ("coarse_4", coarse4_ok),
            ("coarse_3", coarse3_ok),
            ("entity_exact", entity_exact),
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
    n = len(valid_rows)
    result = {
        "evaluated_rows": n,
        "missing_invalid_rows": len(rows) - n,
    }
    for metric in METRICS[2:]:
        result[metric] = safe_div(counts[metric], n)
    return result


def collect_results():
    return [{"variant": name, **evaluate(read_rows(path))} for name, path in VARIANTS]


def fmt(value):
    return str(value) if isinstance(value, int) else f"{value:.3f}"


def verdict(rows):
    by_name = {row["variant"]: row for row in rows}
    combined = by_name["combined_v3"]
    r6 = by_name["R6"]
    checks = {
        "role_beats_combined": r6["role"] > combined["role"],
        "relaxed_1_beats_combined": r6["relaxed_1"] > combined["relaxed_1"],
        "relaxed_2_matches_or_beats_combined": r6["relaxed_2"] >= combined["relaxed_2"],
        "relaxed_3_matches_or_beats_combined": r6["relaxed_3"] >= combined["relaxed_3"],
        "strict_not_lower_than_combined": r6["strict"] >= combined["strict"],
    }
    if all(checks.values()):
        return "promote R6 as RouteMap v2 candidate", checks
    hard_fail = (
        r6["role"] <= combined["role"]
        and r6["relaxed_1"] <= combined["relaxed_1"]
        and r6["strict"] < combined["strict"]
    )
    if hard_fail:
        return "reject R6 as overfit", checks
    return "keep R6 provisional pending larger split", checks


def write_outputs(rows, final_verdict, checks):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["variant", *METRICS])
        writer.writeheader()
        writer.writerows(rows)

    headers = ["variant", *METRICS]
    lines = [
        "# Heldout R6 Generalisation Comparison",
        "",
        "## Metrics",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join([row["variant"], *[fmt(row[metric]) for metric in METRICS]]) + " |")

    lines.extend([
        "",
        "## Calibration Targets",
        "",
        "| variant | role | coarse_3 | strict | relaxed_1 | relaxed_2 | relaxed_3 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for name, target in CALIBRATION_TARGETS.items():
        lines.append(
            f"| {name} | {target['role']:.3f} | {target['coarse_3']:.3f} | "
            f"{target['strict']:.3f} | {target['relaxed_1']:.3f} | "
            f"{target['relaxed_2']:.3f} | {target['relaxed_3']:.3f} |"
        )

    lines.extend(["", "## R6 Generalisation Checks", "", "| check | passed |", "|---|---:|"])
    for key, passed in checks.items():
        lines.append(f"| {key} | {'YES' if passed else 'NO'} |")
    lines.extend([
        "",
        "## Final Verdict",
        "",
        final_verdict,
        "",
        "The heldout split is `data/v1/gold/expanded_test_v2.csv`, an existing 84-row full-extraction test split with no HELDOUT2 calibration segment overlap.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_table(rows, final_verdict, checks):
    print("heldout_r6_comparison")
    print(",".join(["variant", *METRICS]))
    for row in rows:
        print(",".join([row["variant"], *[fmt(row[metric]) for metric in METRICS]]))
    print("r6_generalisation_checks")
    for key, passed in checks.items():
        print(f"{key}: {'YES' if passed else 'NO'}")
    print(f"final_verdict={final_verdict}")
    print(f"comparison_md={OUT_MD.relative_to(ROOT)}")
    print(f"comparison_csv={OUT_CSV.relative_to(ROOT)}")


def main():
    rows = collect_results()
    final_verdict, checks = verdict(rows)
    write_outputs(rows, final_verdict, checks)
    print_table(rows, final_verdict, checks)


if __name__ == "__main__":
    main()
