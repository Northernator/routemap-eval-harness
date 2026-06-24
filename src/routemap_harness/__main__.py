"""Command line entrypoint for routemap-harness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .core import append_audit_record, harness_check, route_tokens, validate_config
from .policy import repair_stub, summarize_stub


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT = ROOT / "data" / "outputs" / "audit.jsonl"
DEFAULT_SCHEMA = ROOT / "schemas" / "harness_decision_v1.schema.json"


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            return _cmd_check(args)
        if args.command == "repair":
            print(_json(repair_stub(args.decision_id)))
            return 0
        if args.command == "route":
            return _cmd_route(args)
        if args.command == "summarize":
            print(_json(summarize_stub(args.audit)))
            return 0
        if args.command == "validate-config":
            return _cmd_validate_config(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    parser.print_help(sys.stderr)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="routemap-harness")
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser("check")
    check.add_argument("--task", required=True)
    check.add_argument("--schema")
    check.add_argument("--strict", action="store_true")
    check.add_argument("--risk", choices=("low", "high"), default="low")
    check.add_argument("--input", default="-")
    check.add_argument("--audit", default=str(DEFAULT_AUDIT))

    repair = subcommands.add_parser("repair")
    repair.add_argument("--decision-id", required=True)

    route = subcommands.add_parser("route")
    route.add_argument("--passage", required=True)
    route.add_argument("--question", required=True)
    route.add_argument("--router", choices=("element", "token"), default="element")

    summarize = subcommands.add_parser("summarize")
    summarize.add_argument("--audit", default=str(DEFAULT_AUDIT))

    subcommands.add_parser("validate-config")
    return parser


def _cmd_check(args: argparse.Namespace) -> int:
    payload = _load_payload(args.input)
    payload["task_type"] = args.task
    if args.schema:
        payload["schema"] = _load_json_file(args.schema)
    decision = harness_check(payload, risk=args.risk, strict=args.strict)
    append_audit_record(args.audit, decision)
    print(decision.to_json())
    return 1 if decision.is_blocking() else 0


def _cmd_route(args: argparse.Namespace) -> int:
    passage = Path(args.passage).read_text(encoding="utf-8")
    print(_json(route_tokens(passage, args.question, router=args.router)))
    return 0


def _cmd_validate_config(args: argparse.Namespace) -> int:
    result = validate_config(DEFAULT_SCHEMA)
    print(_json(result))
    return 0 if result["ok"] else 1


def _load_payload(path: str) -> dict[str, Any]:
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("input payload is empty")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("input payload must be a JSON object")
    return payload


def _load_json_file(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
