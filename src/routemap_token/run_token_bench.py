"""CLI for TokenRouteQA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bench import card, run_benchmark


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="routemap_token")
    parser.add_argument("run", nargs="?")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default=None)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    out = Path(args.out) if args.out else None
    trace_path = out / "token_importance_traces.jsonl" if out else None
    result = run_benchmark(root=args.root, trace_path=trace_path, seed=args.seed)
    text = card(result)
    print(text)
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / "token_routeqa_card.md").write_text(text, encoding="utf-8")
        summary = dict(result)
        summary.pop("trace_rows", None)
        (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
