import csv
from pathlib import Path


OLLAMA_PATH = Path("data/v1/llm_eval/predictions/ollama_llama31_full_v2_predictions.csv")
ENTITY_PATH = Path("data/v1/gold/entity_extraction_predictions_fresh.csv")
COMBINED_PATH = Path("data/v1/gold/heldout_full_extraction_pred_combined_v3_fresh.csv")
OUT_DIR = Path("data/v1/hybrid/field_ablation/predictions")

REQUIRED_OLLAMA = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "pred_role",
    "pred_operative_status",
    "pred_relation",
    "pred_answer_relevant",
    "pred_valid",
]
REQUIRED_ENTITY = ["segment_id", "pred_entities_ontology_v1"]
REQUIRED_COMBINED = [
    "segment_id",
    "pred_operative_status_combined_v3",
    "pred_relation_combined_v3",
    "pred_answer_relevant_combined_v3",
]

VARIANTS = {
    "A_ollama_role_ontology_entities_ollama_other": {
        "status": "ollama",
        "relation": "ollama",
        "answer": "ollama",
    },
    "B_add_combined_status": {
        "status": "combined",
        "relation": "ollama",
        "answer": "ollama",
    },
    "C_add_combined_relation": {
        "status": "ollama",
        "relation": "combined",
        "answer": "ollama",
    },
    "D_add_combined_answer": {
        "status": "ollama",
        "relation": "ollama",
        "answer": "combined",
    },
    "E_combined_status_relation_answer": {
        "status": "combined",
        "relation": "combined",
        "answer": "combined",
    },
}


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def require_columns(rows, required, label):
    if not rows:
        raise ValueError(f"{label} has no rows")
    missing = [column for column in required if column not in rows[0]]
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def index_by_segment(rows, label):
    result = {}
    for row in rows:
        segment_id = row.get("segment_id", "")
        if not segment_id:
            raise ValueError(f"{label} has row without segment_id")
        if segment_id in result:
            raise ValueError(f"{label} has duplicate segment_id: {segment_id}")
        result[segment_id] = row
    return result


def pick(kind, field, ollama_row, combined_row):
    if kind == "ollama":
        return ollama_row[field]
    if field == "pred_operative_status":
        return combined_row["pred_operative_status_combined_v3"]
    if field == "pred_relation":
        return combined_row["pred_relation_combined_v3"]
    if field == "pred_answer_relevant":
        return combined_row["pred_answer_relevant_combined_v3"]
    raise ValueError(f"Unsupported field: {field}")


def build_variant(name, config, ollama_rows, entities, combined):
    output = []
    for row in ollama_rows:
        segment_id = row["segment_id"]
        if segment_id not in entities:
            raise ValueError(f"Missing ontology entity row for {segment_id}")
        if segment_id not in combined:
            raise ValueError(f"Missing combined_v3 row for {segment_id}")
        combined_row = combined[segment_id]
        out = dict(row)
        out["pred_role"] = row["pred_role"]
        out["pred_entities"] = entities[segment_id]["pred_entities_ontology_v1"]
        out["pred_operative_status"] = pick(config["status"], "pred_operative_status", row, combined_row)
        out["pred_relation"] = pick(config["relation"], "pred_relation", row, combined_row)
        out["pred_answer_relevant"] = pick(config["answer"], "pred_answer_relevant", row, combined_row)
        out["pred_rationale"] = (
            f"Field ablation {name}: role=ollama_full_v2; entities=ontology_v1; "
            f"status={config['status']}; relation={config['relation']}; answer={config['answer']}."
        )
        out["pred_provider"] = f"field_ablation_{name}"
        out["pred_model"] = "ollama_llama3.1_role_plus_ontology_v1_entities_field_ablation"
        out["pred_valid"] = row.get("pred_valid", "YES") or "YES"
        out["pred_errors"] = row.get("pred_errors", "")
        output.append(out)
    return output


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    ollama_rows = read_rows(OLLAMA_PATH)
    entity_rows = read_rows(ENTITY_PATH)
    combined_rows = read_rows(COMBINED_PATH)
    require_columns(ollama_rows, REQUIRED_OLLAMA, str(OLLAMA_PATH))
    require_columns(entity_rows, REQUIRED_ENTITY, str(ENTITY_PATH))
    require_columns(combined_rows, REQUIRED_COMBINED, str(COMBINED_PATH))
    entities = index_by_segment(entity_rows, "ontology entity predictions")
    combined = index_by_segment(combined_rows, "combined_v3 predictions")

    for name, config in VARIANTS.items():
        rows = build_variant(name, config, ollama_rows, entities, combined)
        out_path = OUT_DIR / f"{name}_predictions.csv"
        write_rows(out_path, rows)
        print(f"{name}: {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
