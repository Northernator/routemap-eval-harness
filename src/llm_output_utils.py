import json

from llm_output_parsing import extract_json_object_from_text
from routemap_extraction_contract import is_error_like_output, normalize_extraction, validate_extraction


ERROR_TEXT = [
    "connection refused",
    "max retries",
    "econnrefused",
    "failed to connect",
    "provider error",
    "httpconnectionpool",
]


def read_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8-sig") as source:
        for line_number, line in enumerate(source, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append((line_number, json.loads(line), ""))
            except json.JSONDecodeError as exc:
                rows.append((line_number, {}, f"invalid json line: {exc}"))
    return rows


def find_first_json_object(text):
    parsed, error = extract_json_object_from_text(text)
    return parsed, error or ""


def _validate_candidate(candidate):
    if isinstance(candidate, dict) and "extraction" in candidate:
        candidate = candidate.get("extraction")
    if is_error_like_output(candidate):
        return normalize_extraction({}), False, ["provider_error_like_output"]
    normalized = normalize_extraction(candidate)
    valid, errors = validate_extraction(normalized)
    return normalized, valid, errors


def parse_extraction(record):
    if record.get("provider_error") is True or is_error_like_output(record):
        return normalize_extraction({}), False, ["provider_error_like_output"]
    if "extraction" in record:
        extraction = record.get("extraction")
        return _validate_candidate(extraction)
    elif "raw_response" in record:
        raw = record.get("raw_response", "")
        raw_lower = str(raw).lower()
        if any(pattern in raw_lower for pattern in ERROR_TEXT):
            return normalize_extraction({}), False, ["provider_error_like_output"]
        extraction, parse_error = find_first_json_object(raw)
        if extraction is None:
            return normalize_extraction({}), False, [f"raw_response parse error: {parse_error}"]
    else:
        return normalize_extraction({}), False, ["missing extraction or raw_response"]
    return _validate_candidate(extraction)


def rows_by_segment(jsonl_rows):
    by_segment = {}
    errors = []
    for line_number, record, line_error in jsonl_rows:
        if line_error:
            errors.append((line_number, "", line_error))
            continue
        segment_id = record.get("segment_id", "")
        if not segment_id:
            errors.append((line_number, "", "missing segment_id"))
            continue
        by_segment[segment_id] = (line_number, record)
    return by_segment, errors
