import json
import re


def extract_json_object_from_text(text: str) -> tuple[dict | None, str | None]:
    value = "" if text is None else str(text)
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", value, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        candidate = fence.group(1)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed, None
            return None, "first fenced JSON value is not an object"
        except json.JSONDecodeError:
            pass

    start = value.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(value)):
            char = value[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = value[start:index + 1]
                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, dict):
                            return parsed, None
                        return None, "first balanced JSON value is not an object"
                    except json.JSONDecodeError:
                        break
        start = value.find("{", start + 1)
    return None, "no parseable JSON object found"
