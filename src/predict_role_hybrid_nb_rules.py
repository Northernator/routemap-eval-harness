import csv
from pathlib import Path

from role_classifier_v4 import classify_role_v4
from train_role_nb_baseline import TEST_PATH, TRAIN_PATHS, predict_role, read_rows, train_nb


OUT_PATH = Path("data/v1/gold/heldout_role_hybrid_nb_rules_pred_v2_fresh.csv")
MARGIN = 1.500


def main():
    train_rows = read_rows(TRAIN_PATHS)
    test_rows = read_rows([TEST_PATH])
    model = train_nb(train_rows)

    output_rows = []
    overrides = 0
    correct = 0
    for row in test_rows:
        rule_pred = classify_role_v4(row.get("text", ""), row.get("title", ""))
        nb_pred, nb_margin, _ = predict_role(model, row.get("text", ""))
        hybrid_pred = rule_pred
        if rule_pred == "CLAIM" and nb_pred != "CLAIM" and nb_margin >= MARGIN:
            hybrid_pred = nb_pred
            overrides += 1
        if hybrid_pred == row.get("gold_role", "").strip():
            correct += 1
        output_rows.append({
            "segment_id": row.get("segment_id", ""),
            "title": row.get("title", ""),
            "text": row.get("text", ""),
            "gold_role": row.get("gold_role", ""),
            "pred_role_rule": rule_pred,
            "pred_role_nb": nb_pred,
            "nb_margin": f"{nb_margin:.6f}",
            "pred_role_hybrid": hybrid_pred,
            "notes": row.get("notes", ""),
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=[
                "segment_id",
                "title",
                "text",
                "gold_role",
                "pred_role_rule",
                "pred_role_nb",
                "nb_margin",
                "pred_role_hybrid",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(output_rows)

    accuracy = correct / len(test_rows) if test_rows else 0.0
    print(f"Training rows: {model['total_rows']}")
    print(f"Test rows: {len(test_rows)}")
    print(f"Confidence margin: {MARGIN:.3f}")
    print(f"NB overrides: {overrides}")
    print(f"Hybrid role accuracy: {accuracy:.3f}")
    print(f"Wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
