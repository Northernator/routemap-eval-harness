"""Small expression parser for Digital Route CLI inputs."""

from __future__ import annotations

import re
from typing import Any


def parse_expression(text: str) -> tuple[dict[str, Any], int | None]:
    value = str(text).strip()
    if not value:
        raise ValueError("expression must not be empty")
    expr_text, modulus = _split_modulus(value)
    compact = re.sub(r"\s+", "", expr_text)
    power = _parse_power(compact)
    if power is not None:
        return (
            {
                "family": "power",
                "base": power[0],
                "exponent": power[1],
            },
            modulus,
        )
    fib = re.fullmatch(r"fib(?:onacci)?\((?P<n>\d+)\)", compact, flags=re.IGNORECASE)
    if fib:
        return ({"family": "fibonacci", "n": int(fib.group("n"))}, modulus)
    factorial = compact[:-1] if compact.endswith("!") else ""
    if _is_decimal(factorial):
        return ({"family": "factorial", "n": int(factorial)}, modulus)
    if "*" in compact:
        return ({"family": "bigprod", "values": _parse_int_terms(compact, "*")}, modulus)
    if "+" in compact:
        return ({"family": "bigsum", "values": _parse_int_terms(compact, "+")}, modulus)
    raise ValueError(f"unknown expression form: {text!r}")


def _split_modulus(value: str) -> tuple[str, int | None]:
    end = len(value)
    modulus_start = end
    while modulus_start > 0 and value[modulus_start - 1].isdecimal():
        modulus_start -= 1
    if modulus_start == end or modulus_start == 0 or not value[modulus_start - 1].isspace():
        return value, None

    marker_end = modulus_start
    while marker_end > 0 and value[marker_end - 1].isspace():
        marker_end -= 1
    marker_start = marker_end - 3
    if marker_start < 1 or value[marker_start:marker_end].lower() != "mod":
        return value, None
    if not value[marker_start - 1].isspace():
        return value, None

    expr_end = marker_start
    while expr_end > 0 and value[expr_end - 1].isspace():
        expr_end -= 1
    expr = value[:expr_end].strip()
    modulus = int(value[modulus_start:])
    if modulus is not None and modulus <= 1:
        raise ValueError("modulus must be greater than 1")
    return expr, modulus


def _parse_power(value: str) -> tuple[int, int] | None:
    for separator in ("**", "^"):
        if separator not in value:
            continue
        base, _, exponent = value.partition(separator)
        if _is_signed_decimal(base) and _is_decimal(exponent):
            return int(base), int(exponent)
        return None
    return None


def _is_signed_decimal(value: str) -> bool:
    if value[:1] in {"+", "-"}:
        value = value[1:]
    return _is_decimal(value)


def _is_decimal(value: str) -> bool:
    return bool(value) and all(character.isdecimal() for character in value)


def _parse_int_terms(value: str, separator: str) -> list[int]:
    terms = value.split(separator)
    if len(terms) < 2:
        raise ValueError("compound expression must include at least two terms")
    result: list[int] = []
    for term in terms:
        if not _is_signed_decimal(term):
            raise ValueError(f"invalid integer term: {term!r}")
        result.append(int(term))
    return result


__all__ = ["parse_expression"]
