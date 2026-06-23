"""Command line interface for the RouteMap digital engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .cycles import power_cycle
from .parser import parse_expression
from .residue import fingerprint
from .verify import RULED_OUT_WRONG, verify


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            return _check(args.expr)
        if args.command == "verify":
            return _verify(args.claim, args.strict)
        if args.command == "cycle":
            return _cycle(args.expr)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="routemap")
    subparsers = parser.add_subparsers(dest="command")
    check = subparsers.add_parser("check")
    check.add_argument("expr")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--claim", required=True)
    verify_parser.add_argument("--strict", action="store_true")
    cycle = subparsers.add_parser("cycle")
    cycle.add_argument("expr")
    return parser


def _check(expr: str) -> int:
    expr_spec, modulus = parse_expression(expr)
    if modulus is None:
        print(json.dumps(fingerprint(expr_spec), sort_keys=True))
    else:
        residue = fingerprint(expr_spec, (modulus,))[modulus]
        print(f"{expr} = {residue}")
    return 0


def _verify(path: str, strict: bool) -> int:
    claim = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    expr_spec = claim.get("expr_spec")
    if expr_spec is None:
        if "expr" not in claim:
            raise ValueError("claim must include expr or expr_spec")
        expr_spec, parsed_modulus = parse_expression(str(claim["expr"]))
        if "moduli" not in claim and parsed_modulus is not None:
            claim["moduli"] = [parsed_modulus]
    if "claimed_answer" not in claim:
        raise ValueError("claim must include claimed_answer")
    result = verify(expr_spec, int(claim["claimed_answer"]), claim.get("moduli"))
    print(json.dumps({"verdict": result["verdict"], "disagreeing_moduli": result["disagreeing_moduli"]}, sort_keys=True))
    return 1 if strict and result["verdict"] == RULED_OUT_WRONG else 0


def _cycle(expr: str) -> int:
    expr_spec, modulus = parse_expression(expr.replace("^k", "^1"))
    if expr_spec.get("family") != "power" or modulus is None:
        raise ValueError("cycle expects an expression like '<base>^k mod <m>'")
    cycle = power_cycle(int(expr_spec["base"]), modulus)
    print(json.dumps(cycle, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_parser", "main"]
