import json


def _first_fenced_json_candidate(value: str) -> str | None:
    search_from = 0
    while True:
        opening = value.find("```", search_from)
        if opening == -1:
            return None

        candidate_start = opening + 3
        if value[candidate_start:candidate_start + 4].lower() == "json":
            candidate_start += 4
        while candidate_start < len(value) and value[candidate_start].isspace():
            candidate_start += 1

        if candidate_start < len(value) and value[candidate_start] == "{":
            closing_search_from = candidate_start + 1
            while True:
                closing = value.find("```", closing_search_from)
                if closing == -1:
                    return None
                candidate_end = closing
                while candidate_end > candidate_start and value[candidate_end - 1].isspace():
                    candidate_end -= 1
                if candidate_end > candidate_start and value[candidate_end - 1] == "}":
                    return value[candidate_start:candidate_end]
                closing_search_from = closing + 3

        search_from = opening + 1


def extract_json_object_from_text(text: str) -> tuple[dict | None, str | None]:
    value = "" if text is None else str(text)
    candidate = _first_fenced_json_candidate(value)
    if candidate is not None:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed, None
            return None, "first fenced JSON value is not an object"
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    start = value.find("{")
    while start != -1:
        object_content = start + 1
        while object_content < len(value) and value[object_content].isspace():
            object_content += 1
        if object_content == len(value) or value[object_content] not in {'"', "}"}:
            start = value.find("{", start + 1)
            continue
        try:
            parsed, _ = decoder.raw_decode(value, start)
            if isinstance(parsed, dict):
                return parsed, None
            return None, "first balanced JSON value is not an object"
        except (json.JSONDecodeError, RecursionError):
            pass
        start = value.find("{", start + 1)
    return None, "no parseable JSON object found"
