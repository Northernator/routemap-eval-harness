"""Output extraction helpers for Phase 3 Slice 4."""

from __future__ import annotations

import json
import re

from llm_output_parsing import extract_json_object_from_text


def extract_code(raw: str) -> tuple[str, bool, str]:
    value = "" if raw is None else str(raw)
    fence = re.search(r"```(?:python|py)?\s*(.*?)\s*```", value, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        code = fence.group(1).strip()
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
        final_match = re.search(r"(?:answer|final)\D+(-?\d[\d,]*)", value, flags=re.I)
        if final_match:
            token = final_match.group(1)
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


def _plausibly_code_like(code: str) -> bool:
    markers = ("def ", "class ", "import ", "from ", "return ", "=", "for ", "while ", "if ")
    return any(marker in code for marker in markers)
