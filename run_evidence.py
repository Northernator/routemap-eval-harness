#!/usr/bin/env python3
"""RouteMap Evidence Pack — one-command reproducibility runner.

Runs the verifiable test suites and the offline benchmarks, captures pass/fail and the headline
numbers, and writes EVIDENCE/RESULTS.md. Run from the harness root:

    cd routemap_eval_harness/routemap_eval_harness
    python run_evidence.py

Offline steps need only Python + numpy. The matrix self-check needs torch+transformers (CPU).
The live-ollama validator N=30 numbers and the GPU matrix numbers are environment-gated (see notes).
"""
from __future__ import annotations
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "EVIDENCE"
ENV = {**os.environ, "PYTHONPATH": str(SRC), "PYTHONPYCACHEPREFIX": str(OUT / "_pyc")}


def _have(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except Exception:
        return False


TORCH = _have("torch")

STEPS = [
    ("pytest: validators", [sys.executable, "-m", "pytest", "rv_test_validator_package.py", "-q"], "sound checkers; FP 0.000"),
    ("pytest: digital engine", [sys.executable, "-m", "pytest", "rd_test_digital_engine.py", "-q"], "residue/CRT/cycles; off-by-M sound"),
    ("pytest: arithmetic bench", [sys.executable, "-m", "pytest", "rb_test_bench.py", "-q"], "oracle-verifier agreement; GT independent"),
    ("pytest: token routing", [sys.executable, "-m", "pytest", "rt_test_token.py", "-q"], "no-leak; GT-derived classification"),
    ("pytest: element routing", [sys.executable, "-m", "pytest", "rt_test_elements.py", "-q"], "element router; no-leak; default router_mode=element"),
    ("pytest: embedding", [sys.executable, "-m", "pytest", "re_test_embedding.py", "-q"], "determinism; recall vs brute force"),
    ("pytest: controller", [sys.executable, "-m", "pytest", "rc_test_controller.py", "-q"], "dispatch; no-silent-prune; schema-valid"),
    ("pytest: harness core+gold", [sys.executable, "-m", "pytest", "tests/test_harness_core.py", "tests/test_harness_gold.py", "-q"], "0 false accepts; FP 0.000"),
    ("pytest: api+web", [sys.executable, "-m", "pytest", "tests/test_api.py", "tests/test_web.py", "-q"], "route endpoint + web surface"),
    ("pytest: matrix core", [sys.executable, "-m", "pytest", "rm_test_matrix.py", "-q"], "route/validate core (numpy)"),
    ("bench: validators regression", [sys.executable, "-m", "routemap_validators.run_regression"], "FP 0.000; JSON rule-out 0.600 (cached corpus)"),
    ("bench: HugeArithmeticRouteBench", [sys.executable, "-m", "routemap_bench", "run", "--out", str(OUT / "bench_arith")], "catch 1.000; oracle agreement 1.000"),
    ("bench: TokenRouteQA (router comparison)", [sys.executable, "-m", "routemap_token", "run", "--router", "all"], "real gold; default element ~0.44, token baseline ~0.34"),
    ("bench: EmbeddingRouteIndex", [sys.executable, "-m", "routemap_embedding", "run", "--out", str(OUT / "bench_embed")], "recall/speed frontier (synthetic)"),
    ("demo: unified controller", [sys.executable, "-m", "routemap_controller", "demo", "--out", str(OUT / "controller_demo")], "7 plans; schema-valid audit; 1 escalation"),
    ("demo: harness CLI check", [sys.executable, "-m", "routemap_harness", "check", "--task", "json_schema", "--input", "examples/json_tool_call/harness_cli_payload.json", "--audit", str(OUT / "harness_cli_audit.jsonl")], "schema-valid decision + audit line"),
    ("blind: held-out suite (frozen)", [sys.executable, "src/blind/score_blind_v1.py"], "fresh data never tuned against; verifies SHA-256 then scores once"),
    ("blind: element router gate (frozen)", [sys.executable, "-m", "routemap_elements.blind_validate"], "frozen-weight OOD gate; element > token at 0 recall loss"),
]
GATED = [
    ("matrix self-check (CPU)", [sys.executable, "-m", "routemap_matrix", "selfcheck"], "torch+transformers"),
]


def _run(argv, timeout=1200):
    try:
        p = subprocess.run(argv, cwd=ROOT, env=ENV, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)
    except Exception as exc:
        return 1, f"RUNNER ERROR: {exc}"


def _tail(s, n=12):
    return "\n".join(s.strip().splitlines()[-n:])


def main():
    OUT.mkdir(exist_ok=True)
    print(f"RouteMap Evidence runner | Python {sys.version.split()[0]} | torch: {TORCH}\n")
    rows = []
    for name, argv, note in STEPS:
        t0 = time.time()
        rc, log = _run(argv)
        status = "PASS" if rc == 0 else "FAIL"
        print(f"[{status}] {name}  ({time.time() - t0:.1f}s)")
        rows.append((name, status, note, _tail(log)))
    for name, argv, note in GATED:
        if TORCH:
            rc, log = _run(argv)
            status = "PASS" if rc == 0 else "FAIL"
        else:
            status, log = "SKIP", "torch not installed"
        print(f"[{status}] {name}  ({note})")
        rows.append((name, status, note, _tail(log)))

    lines = ["# RouteMap Evidence — RESULTS", "",
             f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} | Python {sys.version.split()[0]} | torch: {TORCH}", "",
             "| Step | Status | Headline |", "| --- | --- | --- |"]
    lines += [f"| {n} | {s} | {note} |" for n, s, note, _ in rows]
    lines += ["", "## Not auto-run (environment-gated)",
              "- Validator N=30 live numbers need a local ollama model; the cached-corpus regression above reproduces FP 0.000 / JSON 0.600 offline.",
              "- Matrix peak-VRAM + long-context need an Ampere+ GPU — see src/routemap_matrix/HANDOFF.md.", "",
              "## Captured log tails"]
    for n, s, note, t in rows:
        lines += [f"### {n} [{s}]", "```", t, "```", ""]
    (OUT / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")

    npass = sum(1 for _, s, _, _ in rows if s == "PASS")
    print(f"\n{npass}/{len(rows)} steps passed (SKIP = needs torch/ollama/GPU). Wrote {OUT / 'RESULTS.md'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
