"""Output extraction helpers for Phase 3 Slice 4."""

from __future__ import annotations

import json
import re

from llm_output_parsing import extract_json_object_from_text


def _first_fenced_code(value: str) -> str | None:
    opening = value.find("```")
    if opening == -1:
        return None

    code_start = opening + 3
    language = value[code_start:code_start + 6].lower()
    if language.startswith("python"):
        code_start += 6
    elif language.startswith("py"):
        code_start += 2
    while code_start < len(value) and value[code_start].isspace():
        code_start += 1

    closing = value.find("```", code_start)
    if closing == -1:
        return None
    return value[code_start:closing].strip()


def extract_code(raw: str) -> tuple[str, bool, str]:
    value = "" if raw is None else str(raw)
    code = _first_fenced_code(value)
    if code is not None:
        if code:
            return code, True, "first fenced code block"
        return "", False, "empty fenced code block"
    lines = value.strip().splitlines()
    stripped: list[str] = []
    for line in lines:
        lower = line.strip().lower()
        if not stripped and (
            lower.startswith("here is")
            or lower.startswith("sure")
            or lower.startswith("below is")
            or lower.startswith("the code")
        ):
            continue
        if lower.startswith("explanation:") or lower.startswith("note:"):
            break
        stripped.append(line)
    code = "\n".join(stripped).strip()
    if not code:
        return "", False, "no content after prose stripping"
    if _plausibly_code_like(code):
        return code, True, "prose-stripped code-like text"
    return "", False, "no fenced block or plausible Python code found"


def extract_json(raw: str) -> tuple[str, bool, str]:
    parsed, error = extract_json_object_from_text("" if raw is None else str(raw))
    if parsed is None:
        return "", False, error or "no JSON object found"
    return json.dumps(parsed, sort_keys=True, separators=(",", ":")), True, "extracted JSON object"


def extract_integer(raw: str) -> tuple[str, bool, str]:
    value = "" if raw is None else str(raw)
    answer_match = re.search(r'"answer"\s*:\s*"?(?P<answer>-?\d[\d,\s]*)"?', value, flags=re.I)
    if answer_match:
        token = answer_match.group("answer")
    else:
        labeled_token = _extract_labeled_integer(value)
        if labeled_token is not None:
            token = labeled_token
        else:
            tokens = re.findall(r"-?\d[\d,]*", value)
            if not tokens:
                return "", False, "no integer found"
            token = tokens[-1]
    digits = re.sub(r"[,\s]", "", token)
    try:
        int(digits)
    except ValueError:
        return "", False, "integer token did not parse"
    return digits, True, "extracted integer"


def _extract_labeled_integer(value: str) -> str | None:
    for label in re.finditer(r"answer|final", value, flags=re.I):
        digit_start = label.end()
        if digit_start >= len(value) or value[digit_start].isdecimal():
            continue

        while digit_start < len(value) and not value[digit_start].isdecimal():
            digit_start += 1
        if digit_start == len(value):
            return None

        token_start = digit_start - 1 if value[digit_start - 1:digit_start] == "-" else digit_start
        digit_end = digit_start + 1
        while digit_end < len(value) and (value[digit_end].isdecimal() or value[digit_end] == ","):
            digit_end += 1
        return value[token_start:digit_end]
    return None


def _plausibly_code_like(code: str) -> bool:
    markers = ("def ", "class ", "import ", "from ", "return ", "=", "for ", "while ", "if ")
    return any(marker in code for marker in markers)
