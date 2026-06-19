import argparse
from pathlib import Path
import pandas as pd


SUMMARY_COLUMNS = ["metric", "value"]


def split_entities(raw):
    if pd.isna(raw):
        return set()
    return {part.strip().lower() for part in str(raw).split("|") if part.strip()}


def accuracy(left, right):
    if len(left) == 0:
        return 0.0
    return float((left == right).mean())


def jaccard(left, right):
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def confusion_matrix(df, gold_column, pred_column):
    matrix = pd.crosstab(
        df[gold_column].fillna(""),
        df[pred_column].fillna(""),
        rownames=[f"gold_{gold_column}"],
        colnames=[f"pred_{pred_column}"],
        dropna=False,
    )
    return matrix


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--out", default="data/outputs/route_extraction_scores.csv")
    ap.add_argument("--role-confusion-out", default="data/outputs/role_confusion_matrix.csv")
    ap.add_argument("--status-confusion-out", default="data/outputs/status_confusion_matrix.csv")
    ap.add_argument("--relation-confusion-out", default="data/outputs/relation_confusion_matrix.csv")
    args = ap.parse_args()

    gold = pd.read_csv(args.gold, keep_default_na=False)
    pred = pd.read_csv(args.pred, keep_default_na=False)
    pred_columns = [column for column in pred.columns if column == "segment_id" or column.startswith("llm_")]
    df = gold.merge(pred[pred_columns], on="segment_id", how="left")

    for column in ["llm_role", "llm_entities", "llm_operative_status", "llm_relation"]:
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].fillna("")
    if "llm_valid" not in df.columns:
        df["llm_valid"] = ""
    df["llm_valid"] = df["llm_valid"].astype(str).str.lower().isin(["true", "1", "yes"])

    gold_entities = df["gold_entities"].apply(split_entities)
    pred_entities = df["llm_entities"].apply(split_entities) if "llm_entities" in df.columns else pd.Series([set()] * len(df))
    entity_exact = [left == right for left, right in zip(gold_entities, pred_entities)]
    entity_jaccard = [jaccard(left, right) for left, right in zip(gold_entities, pred_entities)]

    summary = pd.DataFrame([
        {"metric": "segments_scored", "value": len(df)},
        {"metric": "role_accuracy", "value": accuracy(df["gold_role"], df["llm_role"])},
        {"metric": "operative_status_accuracy", "value": accuracy(df["gold_operative_status"], df["llm_operative_status"])},
        {"metric": "relation_accuracy", "value": accuracy(df["gold_relation"], df["llm_relation"])},
        {"metric": "entity_exact_match", "value": sum(entity_exact) / len(entity_exact) if entity_exact else 0.0},
        {"metric": "entity_jaccard", "value": sum(entity_jaccard) / len(entity_jaccard) if entity_jaccard else 0.0},
        {"metric": "invalid_output_count", "value": int((~df["llm_valid"]).sum())},
    ], columns=SUMMARY_COLUMNS)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out, index=False)
    confusion_matrix(df, "gold_role", "llm_role").to_csv(args.role_confusion_out)
    confusion_matrix(df, "gold_operative_status", "llm_operative_status").to_csv(args.status_confusion_out)
    confusion_matrix(df, "gold_relation", "llm_relation").to_csv(args.relation_confusion_out)

    print("== route extraction score summary ==")
    print(summary.to_string(index=False))
    print(f"Wrote {args.out}")
    print(f"Wrote {args.role_confusion_out}")
    print(f"Wrote {args.status_confusion_out}")
    print(f"Wrote {args.relation_confusion_out}")


if __name__ == "__main__":
    main()
