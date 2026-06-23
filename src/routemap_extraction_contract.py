from entity_ontology_v1 import normalize_entity


ERROR_LIKE_KEYS = {"error", "exception", "connection_error", "provider_error", "status_code", "traceback"}
ERROR_LIKE_TEXT = [
    "connection refused",
    "max retries",
    "econnrefused",
    "failed to connect",
    "provider error",
    "httpconnectionpool",
    "traceback",
]
ALLOWED_ROLES = ["BACKGROUND", "CLAIM", "DEFINE", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]
ALLOWED_STATUSES = ["ACTIVE", "CONDITIONAL", "LIMITED", "NEGATED", "DESCRIPTIVE"]
ALLOWED_RELATIONS = [
    "sets_context",
    "defines",
    "asserts",
    "recommends",
    "reports_usefulness",
    "limits",
    "warns_about",
    "gives_example",
    "proposes_next_test",
    "maps_to",
    "requires",
    "supports_retrieval",
]
ALLOWED_ANSWER_RELEVANCE = ["YES", "NO", "MAYBE"]


def empty_extraction() -> dict:
    return {
        "role": "BACKGROUND",
        "entities": [],
        "operative_status": "DESCRIPTIVE",
        "relation": "sets_context",
        "answer_relevant": "MAYBE",
        "rationale": "",
    }


def _entity_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        parts = value.split(";")
    elif isinstance(value, list):
        parts = value
    else:
        parts = [str(value)]
    entities = []
    seen = set()
    for part in parts:
        normalized = normalize_entity(str(part).strip())
        if normalized and normalized not in seen:
            seen.add(normalized)
            entities.append(normalized)
    return entities


def normalize_extraction(obj: dict) -> dict:
    base = empty_extraction()
    if not isinstance(obj, dict):
        return base
    merged = {**base, **obj}
    merged["role"] = str(merged.get("role", "")).strip().upper()
    merged["operative_status"] = str(merged.get("operative_status", "")).strip().upper()
    merged["relation"] = str(merged.get("relation", "")).strip()
    merged["answer_relevant"] = str(merged.get("answer_relevant", "")).strip().upper()
    merged["entities"] = _entity_list(merged.get("entities", []))
    merged["rationale"] = str(merged.get("rationale", "")).strip()
    return merged


def is_error_like_output(obj: dict) -> bool:
    if not isinstance(obj, dict):
        return False
    if ERROR_LIKE_KEYS & set(obj):
        return True
    text = " ".join(str(value) for value in obj.values()).lower()
    return any(pattern in text for pattern in ERROR_LIKE_TEXT)


def _is_default_empty_error(normalized: dict) -> bool:
    if not (
        normalized["role"] == "BACKGROUND"
        and normalized["entities"] == []
        and normalized["operative_status"] == "DESCRIPTIVE"
        and normalized["relation"] == "sets_context"
        and normalized["answer_relevant"] == "MAYBE"
    ):
        return False
    rationale = normalized.get("rationale", "")
    if not rationale:
        return True
    lowered = rationale.lower()
    return any(pattern in lowered for pattern in ERROR_LIKE_TEXT)


def validate_extraction(obj: dict) -> tuple[bool, list[str]]:
    if is_error_like_output(obj) and "extraction" not in obj:
        return False, ["provider_error_like_output"]
    normalized = normalize_extraction(obj)
    errors = []
    if _is_default_empty_error(normalized):
        errors.append("default_empty_extraction")
    if normalized["role"] not in ALLOWED_ROLES:
        errors.append(f"invalid role: {normalized['role']}")
    if normalized["operative_status"] not in ALLOWED_STATUSES:
        errors.append(f"invalid operative_status: {normalized['operative_status']}")
    if normalized["relation"] not in ALLOWED_RELATIONS:
        errors.append(f"invalid relation: {normalized['relation']}")
    if normalized["answer_relevant"] not in ALLOWED_ANSWER_RELEVANCE:
        errors.append(f"invalid answer_relevant: {normalized['answer_relevant']}")
    if not isinstance(normalized["entities"], list):
        errors.append("entities must be a list")
    return not errors, errors
