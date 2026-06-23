import argparse
import csv
from pathlib import Path

from entity_ontology_v1 import extract_entities_ontology_v1


DEFAULT_OLLAMA = Path("data/v1/llm_eval/predictions/ollama_llama31_full_v2_predictions.csv")
DEFAULT_ENTITY = Path("data/v1/gold/entity_extraction_predictions_fresh.csv")
DEFAULT_OUT = Path("data/v1/hybrid/predictions/ollama_role_ontology_entity_v1_predictions.csv")

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
]


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def require_columns(rows, columns, label):
    if not rows:
        raise ValueError(f"{label} has no rows")
    missing = [column for column in columns if column not in rows[0]]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def entity_lookup(entity_rows):
    if not entity_rows:
        return {}
    if "segment_id" not in entity_rows[0]:
        raise ValueError("entity prediction source missing required column: segment_id")
    if "pred_entities_ontology_v1" not in entity_rows[0]:
        return {}
    return {row["segment_id"]: row.get("pred_entities_ontology_v1", "") for row in entity_rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ollama-predictions", default=str(DEFAULT_OLLAMA))
    parser.add_argument("--entity-predictions", default=str(DEFAULT_ENTITY))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    ollama_path = Path(args.ollama_predictions)
    entity_path = Path(args.entity_predictions)
    if not ollama_path.exists():
        raise FileNotFoundError(f"Missing Ollama prediction CSV: {ollama_path}")
    ollama_rows = read_rows(ollama_path)
    require_columns(ollama_rows, REQUIRED_OLLAMA, str(ollama_path))

    entities_by_segment = {}
    if entity_path.exists():
        entities_by_segment = entity_lookup(read_rows(entity_path))

    hybrid_rows = []
    missing_entities = []
    for row in ollama_rows:
        out = dict(row)
        segment_id = row["segment_id"]
        ontology_entities = entities_by_segment.get(segment_id)
        if ontology_entities is None:
            ontology_entities = extract_entities_ontology_v1(row.get("text", ""), row.get("title", ""))
            if not ontology_entities:
                missing_entities.append(segment_id)
        out["pred_entities"] = ontology_entities
        out["pred_rationale"] = (
            f"Hybrid: role/status/relation/relevance from Ollama llama3.1; "
            f"entities from ontology_v1. Ollama rationale: {row.get('pred_rationale', '')}"
        )
        out["pred_provider"] = "hybrid_ollama_role_ontology_entity"
        out["pred_model"] = "ollama_llama3.1_role_plus_ontology_v1_entities"
        out["pred_valid"] = row.get("pred_valid", "YES") or "YES"
        out["pred_errors"] = row.get("pred_errors", "")
        hybrid_rows.append(out)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(hybrid_rows[0].keys()))
        writer.writeheader()
        writer.writerows(hybrid_rows)

    print(f"Rows written: {len(hybrid_rows)}")
    print(f"Output: {out_path}")
    print(f"Entity source: {entity_path if entities_by_segment else 'entity_ontology_v1.extract_entities_ontology_v1'}")
    print(f"Rows with empty ontology entities after fallback: {len(missing_entities)}")


if __name__ == "__main__":
    main()
