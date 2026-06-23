"""CLI for TokenRouteQA.

Router modes (default 'token' is the preserved baseline; 'element' / 'codon-gate'
are experimental, pending blind validation before any default change):
    python -m routemap_token run --router token
    python -m routemap_token run --router element
    python -m routemap_token run --router all      # report all three side by side
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bench import card, run_benchmark

ROUTERS = ("token", "element", "codon-gate")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="routemap_token")
    parser.add_argument("run", nargs="?")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--router", default="element", choices=[*ROUTERS, "all"])
    args = parser.parse_args(argv)
    out = Path(args.out) if args.out else None

    if args.router == "all":
        results = {r: run_benchmark(root=args.root, seed=args.seed, router=r) for r in ROUTERS}
        lines = ["# TokenRouteQA — router comparison (default = token)", "",
                 "| router | reduction @<0.01 | reduction @<0.02 | reduction @<0.05 | recall_loss @<0.01 |",
                 "| --- | ---: | ---: | ---: | ---: |"]
        for r in ROUTERS:
            f = results[r]["frontier"]
            lines.append(f"| {r}{' (default)' if r == 'token' else ''} | "
                         f"{f['lt_0_01']['token_reduction']:.3f} | {f['lt_0_02']['token_reduction']:.3f} | "
                         f"{f['lt_0_05']['token_reduction']:.3f} | {f['lt_0_01']['recall_loss']:.3f} |")
        lines += ["", "token is the preserved baseline/default; element & codon-gate are experimental "
                  "(promote only after out-of-domain/blind validation)."]
        text = "\n".join(lines)
        print(text)
        if out:
            out.mkdir(parents=True, exist_ok=True)
            (out / "router_comparison.md").write_text(text, encoding="utf-8")
            (out / "router_comparison.json").write_text(json.dumps(
                {r: {k: results[r]["frontier"][k] for k in ("lt_0_01", "lt_0_02", "lt_0_05")} for r in ROUTERS},
                indent=2), encoding="utf-8")
        return 0

    trace_path = out / "token_importance_traces.jsonl" if out else None
    result = run_benchmark(root=args.root, trace_path=trace_path, seed=args.seed, router=args.router)
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
