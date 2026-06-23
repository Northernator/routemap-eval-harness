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
    power = re.fullmatch(r"(?P<base>[+-]?\d+)(?:\^|\*\*)(?P<exponent>\d+)", compact)
    if power:
        return (
            {
                "family": "power",
                "base": int(power.group("base")),
                "exponent": int(power.group("exponent")),
            },
            modulus,
        )
    fib = re.fullmatch(r"fib(?:onacci)?\((?P<n>\d+)\)", compact, flags=re.IGNORECASE)
    if fib:
        return ({"family": "fibonacci", "n": int(fib.group("n"))}, modulus)
    factorial = re.fullmatch(r"(?P<n>\d+)!", compact)
    if factorial:
        return ({"family": "factorial", "n": int(factorial.group("n"))}, modulus)
    if "*" in compact:
        return ({"family": "bigprod", "values": _parse_int_terms(compact, "*")}, modulus)
    if "+" in compact:
        return ({"family": "bigsum", "values": _parse_int_terms(compact, "+")}, modulus)
    raise ValueError(f"unknown expression form: {text!r}")


def _split_modulus(value: str) -> tuple[str, int | None]:
    match = re.fullmatch(r"(?P<expr>.+?)(?:\s+mod\s+(?P<modulus>\d+))?", value, flags=re.IGNORECASE)
    if match is None:
        raise ValueError(f"could not parse expression: {value!r}")
    expr = match.group("expr").strip()
    modulus_text = match.group("modulus")
    modulus = None if modulus_text is None else int(modulus_text)
    if modulus is not None and modulus <= 1:
        raise ValueError("modulus must be greater than 1")
    return expr, modulus


def _parse_int_terms(value: str, separator: str) -> list[int]:
    terms = value.split(separator)
    if len(terms) < 2:
        raise ValueError("compound expression must include at least two terms")
    result: list[int] = []
    for term in terms:
        if not re.fullmatch(r"[+-]?\d+", term):
            raise ValueError(f"invalid integer term: {term!r}")
        result.append(int(term))
    return result


__all__ = ["parse_expression"]
