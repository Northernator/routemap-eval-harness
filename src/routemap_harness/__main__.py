"""Command line entrypoint for routemap-harness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from .audit_store import DEFAULT_AUDIT, summarize
from .core import append_audit_record, harness_check, route_tokens, validate_config
from .policy import repair, repair_stub


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            return _cmd_check(args)
        if args.command == "repair":
            return _cmd_repair(args)
        if args.command == "route":
            return _cmd_route(args)
        if args.command == "summarize":
            print(summarize(args.audit)["markdown"])
            return 0
        if args.command == "validate-config":
            return _cmd_validate_config(args)
        if args.command == "serve":
            return _cmd_serve(args)
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
    repair.add_argument("--input")
    repair.add_argument("--audit", default=str(DEFAULT_AUDIT))
    repair.add_argument("--max-retries", type=int, default=2)
    repair.add_argument("--model-output", action="append", default=[])

    route = subcommands.add_parser("route")
    route.add_argument("--passage", required=True)
    route.add_argument("--question", required=True)
    route.add_argument("--router", choices=("element", "token"), default="element")

    summarize = subcommands.add_parser("summarize")
    summarize.add_argument("--audit", default=str(DEFAULT_AUDIT))

    subcommands.add_parser("validate-config")

    serve = subcommands.add_parser("serve", help="run the RouteMap cockpit (FastAPI UI + API) via uvicorn")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true", help="auto-reload on source changes (dev)")
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


def _cmd_repair(args: argparse.Namespace) -> int:
    if not args.input:
        print(_json(repair_stub(args.decision_id)))
        return 0
    payload = _load_payload(args.input)
    outputs = list(args.model_output)
    if not outputs:
        raise ValueError("repair requires at least one --model-output in offline CLI mode")

    def model_fn(_request: Mapping[str, Any]) -> str:
        index = min(len(calls), len(outputs) - 1)
        calls.append(index)
        return outputs[index]

    calls: list[int] = []
    decision = harness_check(payload)
    result = repair(decision, payload, model_fn, max_retries=args.max_retries, audit_path=args.audit)
    print(_json(result.to_dict()))
    return 1 if result.final_decision.is_blocking() else 0


def _cmd_route(args: argparse.Namespace) -> int:
    passage = Path(args.passage).read_text(encoding="utf-8")
    print(_json(route_tokens(passage, args.question, router=args.router)))
    return 0


def _cmd_validate_config(args: argparse.Namespace) -> int:
    result = validate_config()
    print(_json(result))
    return 0 if result["ok"] else 1


def _cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ModuleNotFoundError:
        print("serve needs the API extras: pip install 'routemap-harness[api]'", file=sys.stderr)
        return 2
    print(f"RouteMap cockpit -> http://{args.host}:{args.port}  (Ctrl+C to stop)", file=sys.stderr)
    uvicorn.run("routemap_harness.api:app", host=args.host, port=int(args.port), reload=bool(args.reload))
    return 0


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
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


if __name__ == "__main__":
    raise SystemExit(main())
