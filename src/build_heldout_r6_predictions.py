import csv
import json
import os
from pathlib import Path

from build_combined_full_extraction_v3 import answer_relevant, operative_status
from entity_ontology_v1 import extract_entities_ontology_v1
from generate_llm_extraction_requests import build_prompt
from llm_output_utils import parse_extraction, read_jsonl, rows_by_segment
from role_taxonomies import map_role
from run_live_llm_provider import request_json
from train_role_boundary_augmented_baselines import (
    BASE_TRAIN,
    BOUNDARY_DEV,
    BOUNDARY_TRAIN,
    RESULTS_CSV,
    model_factories,
    prediction_column,
    read_rows,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SPLIT = ROOT / "data/v1/gold/expanded_test_v2.csv"
CALIBRATION_GOLD = ROOT / "data/v1/gold/heldout_full_extraction_gold_v2_adjudicated.csv"
PROMPT_TEMPLATE = ROOT / "data/v1/gold/ROUTEMAP_LLM_EXTRACTION_PROMPT_TEMPLATE.md"
OUT_ROOT = ROOT / "data/v1/heldout/r6_generalisation"
PRED_DIR = OUT_ROOT / "predictions"
REPORT_DIR = OUT_ROOT / "reports"

OLLAMA_MODEL = "llama3.1:latest"
RAW_OLLAMA_OUT = PRED_DIR / "ollama_llama31_heldout_outputs.jsonl"
COMBINED_OUT = PRED_DIR / "combined_v3_heldout_predictions.csv"
D_OUT = PRED_DIR / "D_heldout_predictions.csv"
R6_OUT = PRED_DIR / "R6_heldout_predictions.csv"
PROVENANCE_OUT = REPORT_DIR / "HELDOUT_R6_SPLIT_PROVENANCE.md"

REQUIRED_SPLIT_COLUMNS = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
]

PRED_COLUMNS = [
    "pred_role",
    "pred_entities",
    "pred_operative_status",
    "pred_relation",
    "pred_answer_relevant",
    "pred_rationale",
    "pred_provider",
    "pred_model",
    "pred_valid",
    "pred_errors",
]


def require_columns(rows, required, label):
    if not rows:
        raise ValueError(f"No rows found in required CSV: {label}")
    missing = [column for column in required if column not in rows[0]]
    if missing:
        raise ValueError(f"Missing required columns in {label}: {', '.join(missing)}")


def index_by_segment(rows, label):
    indexed = {}
    for row in rows:
        segment_id = row.get("segment_id", "").strip()
        if not segment_id:
            raise ValueError(f"Blank segment_id in {label}")
        if segment_id in indexed:
            raise ValueError(f"Duplicate segment_id in {label}: {segment_id}")
        indexed[segment_id] = row
    return indexed


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_csv(path, rows, fieldnames=None):
    if not rows:
        raise ValueError(f"Refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames or list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def selected_boundary_model():
    rows = read_rows(RESULTS_CSV)
    overall = [row for row in rows if row.get("metric_type") == "overall"]
    if not overall:
        raise ValueError(f"No overall rows found in {RESULTS_CSV}")
    best = max(overall, key=lambda row: float(row["accuracy"]))
    return best["setting"], best["model"], float(best["accuracy"])


def training_rows_for_setting(setting):
    base_rows = read_rows(BASE_TRAIN)
    if setting == "base_only":
        return base_rows
    if setting == "base_plus_boundary_train":
        return base_rows + read_rows(BOUNDARY_TRAIN)
    if setting == "base_plus_boundary_train_dev":
        return base_rows + read_rows(BOUNDARY_TRAIN) + read_rows(BOUNDARY_DEV)
    raise ValueError(f"Unknown boundary model setting: {setting}")


def boundary_roles_for_heldout(heldout_rows):
    setting, model_name, accuracy = selected_boundary_model()
    factories = model_factories()
    if model_name not in factories:
        raise ValueError(f"Unknown selected boundary model: {model_name}")
    model = factories[model_name]()
    model.fit(training_rows_for_setting(setting))
    column = prediction_column(setting, model_name)
    predictions = {row["segment_id"]: model.predict(row) for row in heldout_rows}
    return predictions, setting, model_name, column, accuracy


def relation_for_role(role):
    return {
        "BACKGROUND": "sets_context",
        "DEFINE": "defines",
        "CLAIM": "asserts",
        "METHOD": "recommends",
        "RESULT": "reports_usefulness",
        "LIMITATION": "limits",
        "NEXT_STEP": "proposes_next_test",
        "EXAMPLE": "gives_example",
    }.get(role, "")


def standard_prediction_row(row, role, entities, status, relation, answer, rationale, provider, model):
    out = dict(row)
    out["pred_role"] = role
    out["pred_entities"] = entities
    out["pred_operative_status"] = status
    out["pred_relation"] = relation
    out["pred_answer_relevant"] = answer
    out["pred_rationale"] = rationale
    out["pred_provider"] = provider
    out["pred_model"] = model
    out["pred_valid"] = "YES"
    out["pred_errors"] = ""
    return out


def build_combined_predictions(heldout_rows):
    roles, setting, model_name, column, accuracy = boundary_roles_for_heldout(heldout_rows)
    output = []
    for row in heldout_rows:
        role = roles[row["segment_id"]]
        output.append(standard_prediction_row(
            row,
            role,
            extract_entities_ontology_v1(row.get("text", ""), row.get("title", "")),
            operative_status(role, row.get("text", "")),
            relation_for_role(role),
            answer_relevant(role, row.get("text", ""), row.get("title", "")),
            f"combined_v3 heldout: fixed boundary role column {column}; ontology_v1 entities; combined_v3 status/relation/answer rules.",
            "combined_v3_heldout",
            f"boundary_augmented_{setting}_{model_name}_selected_at_{accuracy:.3f}",
        ))
    return output, setting, model_name, column, accuracy


def generate_ollama_outputs(heldout_rows):
    existing = {}
    if RAW_OLLAMA_OUT.exists():
        output_rows, line_errors = rows_by_segment(read_jsonl(RAW_OLLAMA_OUT))
        if line_errors:
            preview = "; ".join(f"line {line}: {error}" for line, _, error in line_errors[:5])
            raise ValueError(f"Line errors in existing {RAW_OLLAMA_OUT}: {preview}")
        existing = {segment_id: record for segment_id, (_, record) in output_rows.items()}
    missing_rows = [row for row in heldout_rows if row["segment_id"] not in existing]
    if not missing_rows:
        return "reused_existing_raw_outputs"
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    RAW_OLLAMA_OUT.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if RAW_OLLAMA_OUT.exists() else "w"
    with RAW_OLLAMA_OUT.open(mode, encoding="utf-8", newline="\n") as target:
        for index, row in enumerate(missing_rows, 1):
            prompt = build_prompt(template, row.get("title", ""), row.get("text", ""))
            content = call_ollama_heldout(prompt)
            record = {
                "segment_id": row["segment_id"],
                "provider": "ollama_http",
                "model": OLLAMA_MODEL,
                "raw_response": content,
            }
            target.write(json.dumps(record, ensure_ascii=False) + "\n")
            target.flush()
            print(f"ollama_row={index}/{len(missing_rows)} segment_id={row['segment_id']}")
    return "generated_or_resumed_raw_outputs"


def call_ollama_heldout(prompt):
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    response = request_json(
        f"{host}/api/generate",
        {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=600,
    )
    return response.get("response", json.dumps(response))


def parse_ollama_predictions(heldout_rows):
    output_rows, line_errors = rows_by_segment(read_jsonl(RAW_OLLAMA_OUT))
    if line_errors:
        preview = "; ".join(f"line {line}: {error}" for line, _, error in line_errors[:5])
        raise ValueError(f"Line errors in {RAW_OLLAMA_OUT}: {preview}")

    parsed = {}
    invalid = []
    for row in heldout_rows:
        segment_id = row["segment_id"]
        if segment_id not in output_rows:
            invalid.append(f"{segment_id}: missing output")
            continue
        _, record = output_rows[segment_id]
        extraction, valid, errors = parse_extraction(record)
        if not valid:
            invalid.append(f"{segment_id}: {'; '.join(errors)}")
            continue
        parsed[segment_id] = extraction
    if invalid:
        raise ValueError(f"Invalid/missing Ollama heldout predictions: {' | '.join(invalid[:10])}")
    return parsed


def build_d_predictions(heldout_rows, combined_by_segment, ollama_by_segment):
    output = []
    for row in heldout_rows:
        extraction = ollama_by_segment[row["segment_id"]]
        combined = combined_by_segment[row["segment_id"]]
        output.append(standard_prediction_row(
            row,
            extraction["role"],
            extract_entities_ontology_v1(row.get("text", ""), row.get("title", "")),
            extraction["operative_status"],
            extraction["relation"],
            combined["pred_answer_relevant"],
            "D_add_combined_answer heldout: role/status/relation from Ollama llama3.1; entities=ontology_v1; answer=combined_v3.",
            "D_add_combined_answer_heldout",
            "ollama_llama3.1_role_status_relation_plus_ontology_v1_entities_plus_combined_answer",
        ))
    return output


def build_r6_predictions(heldout_rows, combined_by_segment, d_by_segment):
    output = []
    for row in heldout_rows:
        segment_id = row["segment_id"]
        d_row = d_by_segment[segment_id]
        combined = combined_by_segment[segment_id]
        d_role = d_row["pred_role"]
        combined_role = combined["pred_role"]
        role = combined_role if map_role(d_role, "coarse_3") != map_role(combined_role, "coarse_3") else d_role
        output.append(standard_prediction_row(
            row,
            role,
            d_row["pred_entities"],
            combined["pred_operative_status"],
            combined["pred_relation"],
            combined["pred_answer_relevant"],
            "R6 heldout unchanged: Ollama role with combined_v3 coarse_3 guard; ontology_v1 entities; combined_v3 status/relation/answer.",
            "R6_coarse3_guard_combined_status_relation_heldout",
            "ollama_role_with_combined_v3_coarse3_guard",
        ))
    return output


def validate_no_calibration_overlap(heldout_rows):
    calibration_rows = read_csv(CALIBRATION_GOLD)
    calibration_ids = {
        row["segment_id"]
        for row in calibration_rows
        if row.get("include_in_eval", "YES") == "YES"
    }
    heldout_ids = {row["segment_id"] for row in heldout_rows}
    overlap = sorted(calibration_ids & heldout_ids)
    if overlap:
        raise ValueError(f"Heldout split leaks calibration segment_ids: {', '.join(overlap[:10])}")


def write_provenance(row_count, setting, model_name, column, accuracy, raw_status):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Heldout R6 Generalisation Split Provenance",
        "",
        f"- source split: `{SOURCE_SPLIT.relative_to(ROOT)}`",
        "- split status: existing test split, not newly sampled",
        "- row selection: all rows from `expanded_test_v2.csv`",
        f"- evaluated rows requested: {row_count}",
        "- calibration leakage check: no overlap with `HELDOUT2` calibration segment_ids",
        "- gold files modified: no",
        f"- Ollama model: `{OLLAMA_MODEL}` via local HTTP endpoint",
        f"- Ollama raw output status: {raw_status}",
        f"- combined_v3 boundary-role model: `{setting}` / `{model_name}`",
        f"- selected boundary prediction column: `{column}`",
        f"- selected boundary calibration accuracy: {accuracy:.3f}",
        "- R6 rule: unchanged coarse_3 guard between D/Ollama role and combined_v3 role; ontology_v1 entities; combined_v3 answer/status/relation",
    ]
    PROVENANCE_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    heldout_rows = read_csv(SOURCE_SPLIT)
    require_columns(heldout_rows, REQUIRED_SPLIT_COLUMNS, str(SOURCE_SPLIT))
    validate_no_calibration_overlap(heldout_rows)

    combined_rows, setting, model_name, column, accuracy = build_combined_predictions(heldout_rows)
    write_csv(COMBINED_OUT, combined_rows, list(heldout_rows[0].keys()) + PRED_COLUMNS)
    combined_by_segment = index_by_segment(combined_rows, "combined_v3 heldout")

    raw_status = generate_ollama_outputs(heldout_rows)
    ollama_by_segment = parse_ollama_predictions(heldout_rows)
    d_rows = build_d_predictions(heldout_rows, combined_by_segment, ollama_by_segment)
    write_csv(D_OUT, d_rows, list(heldout_rows[0].keys()) + PRED_COLUMNS)
    d_by_segment = index_by_segment(d_rows, "D heldout")

    r6_rows = build_r6_predictions(heldout_rows, combined_by_segment, d_by_segment)
    write_csv(R6_OUT, r6_rows, list(heldout_rows[0].keys()) + PRED_COLUMNS)
    write_provenance(len(heldout_rows), setting, model_name, column, accuracy, raw_status)

    print("heldout_r6_prediction_build")
    print(f"source_split={SOURCE_SPLIT.relative_to(ROOT)}")
    print(f"heldout_rows={len(heldout_rows)}")
    print(f"combined_predictions={COMBINED_OUT.relative_to(ROOT)}")
    print(f"D_predictions={D_OUT.relative_to(ROOT)}")
    print(f"R6_predictions={R6_OUT.relative_to(ROOT)}")
    print(f"ollama_raw={RAW_OLLAMA_OUT.relative_to(ROOT)}")
    print(f"split_provenance={PROVENANCE_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
