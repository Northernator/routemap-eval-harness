"""CLI for the KV-cache importance-routing benchmark."""
from __future__ import annotations
import argparse


def main(argv=None):
    p = argparse.ArgumentParser(prog="routemap_matrix")
    sub = p.add_subparsers(dest="command")
    r = sub.add_parser("run")
    r.add_argument("--model", default=None)
    r.add_argument("--context-chars", type=int, default=6000)
    r.add_argument("--budgets", default="64,128,256")
    r.add_argument("--policies", default="dense,recency_window,h2o,routemap")
    r.add_argument("--max-new-tokens", type=int, default=12)
    r.add_argument("--efficient", action="store_true", help="memory-efficient SnapKV-style path (capable GPUs)")
    r.add_argument("--obs-window", type=int, default=32)
    r.add_argument("--out", default="data/v1/digital_route/slice_16_matrix")
    s = sub.add_parser("selfcheck")  # CPU toy-model loop check, no download
    args = p.parse_args(argv)
    if args.command == "selfcheck":
        from .selfcheck import selfcheck
        return selfcheck()
    if args.command != "run":
        p.print_help(); return 2
    from .bench import run, report
    result = run(model_name=args.model, context_chars=args.context_chars,
                 budgets=tuple(int(x) for x in args.budgets.split(",")),
                 policies=tuple(args.policies.split(",")), max_new_tokens=args.max_new_tokens, out=args.out,
                 efficient=args.efficient, obs_window=args.obs_window)
    print(report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = ["main"]
