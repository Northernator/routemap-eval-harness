import csv
from pathlib import Path

from compare_heldout_r6_results import METRICS, evaluate, fmt


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "data/v1/heldout/natural_language_blind/r6_generalisation"
PRED_DIR = RUN_ROOT / "predictions"
REPORT_DIR = RUN_ROOT / "reports"
OUT_MD = REPORT_DIR / "NATURAL_BLIND_R6_COMPARISON.md"
OUT_CSV = REPORT_DIR / "natural_blind_r6_comparison.csv"

VARIANTS = [
    ("combined_v3", PRED_DIR / "combined_v3_natural_blind_predictions.csv"),
    ("D_add_combined_answer", PRED_DIR / "D_natural_blind_predictions.csv"),
    ("R6", PRED_DIR / "R6_natural_blind_predictions.csv"),
]


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required predictions file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"No rows found in required predictions file: {path}")
    return rows


def collect_results():
    return [{"variant": name, **evaluate(read_rows(path))} for name, path in VARIANTS]


def verdict(rows):
    by_name = {row["variant"]: row for row in rows}
    combined = by_name["combined_v3"]
    r6 = by_name["R6"]
    checks = {
        "role_beats_combined": r6["role"] > combined["role"],
        "coarse_3_preserved_or_improved": r6["coarse_3"] >= combined["coarse_3"],
        "relaxed_1_beats_combined": r6["relaxed_1"] > combined["relaxed_1"],
        "relaxed_2_matches_or_beats_combined": r6["relaxed_2"] >= combined["relaxed_2"],
        "relaxed_3_matches_or_beats_combined": r6["relaxed_3"] >= combined["relaxed_3"],
        "strict_not_lower_than_combined": r6["strict"] >= combined["strict"],
    }
    if all(checks.values()):
        return "promote R6 as RouteMap v2 default candidate", checks
    hard_fail = (
        r6["role"] <= combined["role"]
        and r6["relaxed_1"] <= combined["relaxed_1"]
        and r6["strict"] < combined["strict"]
    )
    if hard_fail:
        return "reject R6 as overfit or unstable", checks
    return "keep R6 provisional pending more data", checks


def write_outputs(rows, final_verdict, checks):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["variant", *METRICS])
        writer.writeheader()
        writer.writerows(rows)

    headers = ["variant", *METRICS]
    lines = [
        "# Natural Blind R6 Generalisation Comparison",
        "",
        "## Metrics",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join([row["variant"], *[fmt(row[metric]) for metric in METRICS]]) + " |")
    lines.extend(["", "## R6 Generalisation Checks", "", "| check | passed |", "|---|---:|"])
    for key, passed in checks.items():
        lines.append(f"| {key} | {'YES' if passed else 'NO'} |")
    lines.extend([
        "",
        "## Final Verdict",
        "",
        final_verdict,
        "",
        "The split is `data/v1/heldout/natural_language_blind/natural_language_blind_gold.csv`: a 99-row constructed pseudo-blind natural route-note split. It is distinct from HELDOUT2 calibration and EXPAND boundary-stress rows, but it is not a true newly collected blind benchmark.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_table(rows, final_verdict, checks):
    print("natural_blind_r6_comparison")
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
