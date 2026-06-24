# RouteMap Harness v0.1 — Build Review + Agent Prompts

Reviewed against the live repo at `routemap_eval_harness/routemap_eval_harness/` (git HEAD `6861ef0`, working tree clean). This file flags issues in the roadmap, adds what's missing, settles the folder question, and gives paste-ready agent prompts.

---

## TL;DR verdict

The roadmap is sound and the strategy ("build the harness, not the model") is right. **The single biggest risk is that it reads as if you're starting from zero — you are not.** `route_decide()`, `check_output()`, the verdict contract, two audit schemas, and a working repair-prompt builder already exist. If the agents build a parallel stack instead of wrapping the existing one, you'll get drift and two sources of truth. Every prompt below is written to **import and wrap**, never re-implement.

**Folder question: do NOT start a new repo.** The harness must import the six existing packages, so it lives in the same repo as a new package `src/routemap_harness/`. New directories are listed in Prompt 0.

---

## What already exists (so we don't rebuild it)

| Roadmap asks for | Already in repo | Implication |
| --- | --- | --- |
| WP1 "create route_decide orchestrator" | `src/routemap_controller/controller.py` → `route_decide(input, task, *, budget, risk, router_mode)` returning `ActionPlan` with a schema-valid `record` | WP1 = **wrap**, not create |
| Sound-checker validate | `src/routemap_validators/__init__.py` → `check_output(raw, task_type, spec=, object_id=, model=)` → `Decision(verdict, reason, checker)` | Harness calls this; no new checker logic |
| Verdict vocabulary | `dr_verifier_v1.py` + `routemap_validators/verdicts.py` → `RULED_OUT_WRONG`, `NOT_RULED_OUT`, `UNCHECKABLE` (three, one-sided) | Don't add ACCEPT/ESCALATE as verdicts (see Issue 2) |
| WP4 repair loop | `dr_repair_wrapper_v1.py` → `build_repair_prompt()` already does arithmetic/json/code field-specific prompts | WP4 = **migrate/wrap** this |
| Checker framework | `dr_checker_framework_v1.py`, `dr_checker_schema_v1.py`, `dr_checker_code_v1.py`, `dr_residue_engine_v1.py` | Reuse; don't re-author checkers |
| Audit | `routemap_controller/audit.py` (`route_decision_v1`) **and** `routemap_validators/audit.py` (`validator_audit_v1`) | Two schemas already — must reconcile (Issue 3) |
| Classifier | `routemap_controller/classify.py` → `classify()` with the exact six task types | Reuse as-is |
| Token/element default | `routemap_token` with `router_mode` default **element**, token via `--router token`; frozen, validated | Already resolved (Issue 5) |

Not present yet, genuinely new: `routemap_harness` package, a unified `routemap-harness` CLI, FastAPI service, a `model_fn` adapter contract, a single canonical harness audit record, and a CI-locked "zero false accepts" gold set.

---

## Issues to fix in the roadmap

**1. WP1 wording invites a rewrite.** "Create routemap_harness that wraps controller…" is fine, but the DoD ("one importable `check_output()`") collides with the validators' existing `check_output`. Rename the harness entrypoint to `harness_check(payload)` (or `check_payload`) so it's unambiguous, and make WP1's DoD explicitly "imports `routemap_controller.route_decide` and adds repair/escalation/audit around it — no routing logic re-implemented."

**2. §6 conflates verdicts with actions — this breaks the one-sided discipline.** The schema lists five "verdicts" including `ESCALATE` and `ACCEPT_AFTER_CHECK`. In the code a *verdict* is strictly one-sided (`RULED_OUT_WRONG` / `NOT_RULED_OUT` / `UNCHECKABLE`). `accept`, `repair`, `retry`, `escalate`, `reject`, `full_compute` are **actions**; `accepted/rejected/escalated/repaired/failed` are **final_status**. Keep three columns and keep `verdict` to the three one-sided values. A checker must never be able to emit "ACCEPT" — that's a policy decision, not a verification result.

**3. There are already two audit schemas; the roadmap invents a third name without reconciling them.** `route_decision_v1` (controller) and `validator_audit_v1` (validators) both exist with their own `validate_record()`. WP0 currently only says "align docs." It must also: define one canonical `harness_decision_v1` that **embeds** the lane record under a `validator_record` field, ship a crosswalk, and make the summarizer read the canonical record. Otherwise audit aggregation can't span lanes.

**4. Duplicate WP8.** "Benchmark/demo pack" and "Model runner adapters" are both numbered WP8 (and §15 says "Add this as WP8"). Renumber: demo pack = **WP8**, model-runner adapters = **WP9**.

**5. §13 treats `router_mode` default as unresolved — it's resolved.** Element is the validated default (folded into `routemap_token`, frozen weights, blind + two real held-out sets at 0 recall loss; it's literally the HEAD commit). Update §13 to "default is element; expose token baseline via `--router token`" and mark the matching non-goal as satisfied.

**6. The `dr_*` prototype is the closest thing to the harness and is absent from the §13 integration table.** Add rows for `dr_repair_wrapper_v1` (→ WP4 repair), `dr_checker_framework_v1` / `dr_checker_schema_v1` / `dr_checker_code_v1` (→ checker registry), `dr_residue_engine_v1`. The instruction to agents should be "migrate these behind the harness, then delete the standalone duplicates in a later cleanup," not "write repair from scratch."

**7. No explicit "never execute model code" invariant.** §5/§9 say "AST-safe checks" but never state the rule. Make it a hard invariant: code lane uses `ast.parse` only — never `exec`, `eval`, `compile`-and-run, or `import` of model output. Add a test that greps the harness for those calls on model strings.

**8. FastAPI is an uncommitted dependency.** Zero `fastapi` references today and it's in no requirements file. Add `requirements-api.txt` (fastapi, uvicorn, pydantic) so the core stays numpy-only, and make the API import the same core functions (no logic in the route handlers).

**9. "Zero false accepts" is claimed but not CI-enforced.** Add a locked gold fixture set with ground truth and a regression test that fails if any wrong output is accepted; wire it into `run_evidence.py`. A claim that isn't a failing test is a press release.

**10. No packaging / entry point for the CLI.** Today everything runs `PYTHONPATH=src python -m <pkg>`. Stay consistent: ship `python -m routemap_harness …` as the primary surface (matches AGENTS.md), and add an optional `[project.scripts] routemap-harness=…` in a minimal `pyproject.toml` so the `routemap-harness` name in the roadmap also works.

---

## Useful additions (not in the roadmap)

- **A) Commit the schema as a file.** `schemas/harness_decision_v1.schema.json` + a `validate_record()` every emit path calls. Makes "100% schema-valid audit" a test, not a hope.
- **B) Timing/cost fields in the record.** §6 has no timing columns but §11 evaluates latency. Add `latency_ms` (required) and optional `tokens`, `cost_usd` so the summarizer can report p50/p95.
- **C) Offline/no-network guard on the core.** Mirror AGENTS.md: the core check path must be deterministic and make zero network calls; all model I/O sits behind `model_fn`. Add a test that asserts the core path opens no sockets.
- **D) Content-addressed IDs.** Derive `decision_id` from `(input_hash, repair_attempt)` so re-runs are reproducible and repair chains link deterministically.
- **E) Anti-repair-hallucination test (§14 risk → test).** After a repair, re-run *full* validation and assert no previously-valid field changed. Ship as a test, not just a prompt sentence.
- **F) `validate-config` spec.** WP2 lists the command but not its job: validate the schema file, the lane registry, and that every `task_type` maps to ≥1 validator or to an explicit escalation — fail if any lane is silently unmapped.
- **G) Strict / fail-closed exit codes.** `--strict` makes `UNCHECKABLE` and `unknown`/high-risk return a non-zero exit so CI and agents can gate on "nothing passed unverified."
- **H) One fixture per lane as the WP1 done-gate.** A 6-row matrix (arithmetic, json_schema, python_code, extraction, long_context_qa, retrieval) that must each return a schema-valid decision before WP1 is "done."

---

## Corrected work-package sequence

WP0 repo+schema reconciliation → WP1 harness core (wrap `route_decide`) → WP2 CLI → WP4 repair (migrate `dr_repair_wrapper`) → WP5 escalation policy → WP6 audit store + summarizer + schema file → WP9 model_fn adapters → WP3 API → WP8 demo pack + evidence wiring → acceptance sweep. (Repair before API because the API just wraps the core; the core isn't done until repair+escalation land.)

---

# Agent prompts (paste one at a time)

Conventions baked into every prompt — repeat them to the agent if it drifts:

- **Repo root** = `routemap_eval_harness/routemap_eval_harness/` (the dir with `.git`, `src/`, `run_evidence.py`). All paths below are relative to it. **Do not create a new repository.**
- Run with `PYTHONPATH=src`. Python 3.11, Windows/PowerShell. Standard library + numpy only for the core; isolate extra deps in their own requirements file.
- **Import, don't re-implement.** The harness wraps `routemap_controller` and `routemap_validators`. No routing/checker logic is copied into the harness.
- **Verdicts are one-sided:** only `RULED_OUT_WRONG`, `NOT_RULED_OUT`, `UNCHECKABLE`. `accept/repair/retry/escalate/reject/full_compute` are *actions*; `accepted/rejected/escalated/repaired/failed` are *final_status*. Never add a verdict that asserts correctness.
- **Never execute model output.** Code lane is `ast.parse` only.
- Every new behavior ships with a pytest test and a one-line note in `EVIDENCE_PACK.md`. Keep the default path offline and deterministic.

---

### Prompt 0 — Scaffold (folders, schema, requirements)

```
Work in repo root routemap_eval_harness/routemap_eval_harness/ (the dir containing .git, src/, run_evidence.py). Do NOT create a new repo.

Create these new directories and files, empty/stub where noted:
- src/routemap_harness/__init__.py
- src/routemap_harness/core.py          # stub: harness_check(payload) -> Decision (fill in Prompt 1)
- src/routemap_harness/policy.py         # stub: repair + escalation policy (Prompts 4,5)
- src/routemap_harness/audit_store.py    # stub: JSONL writer + summarizer (Prompt 6)
- src/routemap_harness/adapters.py       # stub: model_fn contract (Prompt 9)
- src/routemap_harness/__main__.py       # stub: CLI entry (Prompt 2)
- schemas/harness_decision_v1.schema.json
- examples/json_tool_call/  examples/arithmetic/  examples/extraction/  examples/long_context/   (empty dirs with a .gitkeep)
- data/harness_gold/.gitkeep
- requirements-api.txt   -> fastapi, uvicorn, pydantic
- pyproject.toml (minimal) with [project] name routemap-harness and [project.scripts] routemap-harness = "routemap_harness.__main__:main"

For schemas/harness_decision_v1.schema.json define a JSON Schema (draft 2020-12) with required fields:
schema_version (const "harness_decision_v1"), decision_id, timestamp, task_type
(enum: arithmetic, json_schema, python_code, extraction, long_context_qa, retrieval, unknown),
route_family (enum: digital_residue, sound_checker, token_element, embedding, full_compute, human_review),
verdict (enum: RULED_OUT_WRONG, NOT_RULED_OUT, UNCHECKABLE),
action (enum: accept, repair, retry, escalate, reject, full_compute),
final_status (enum: accepted, rejected, escalated, repaired, failed),
validator (string, may be empty only when action=escalate on unknown),
reason (string), input_hash (string), repair_attempt (integer >=0), latency_ms (number);
optional: model, tokens, cost_usd, validator_record (object).

Do not wire anything yet. Add a pytest tests/test_scaffold.py asserting the schema file loads as valid JSON and the package imports.
```

### Prompt 1 — Harness core (wrap `route_decide`)

```
Implement src/routemap_harness/core.py.

Public API: harness_check(payload: dict, *, budget="balanced", risk="low", router_mode=None, strict=False) -> HarnessDecision

It MUST call routemap_controller.route_decide(...) to do classification, routing, and validation. Do not re-implement any routing or checker logic. Take the ActionPlan it returns and map it onto a HarnessDecision dataclass whose fields match schemas/harness_decision_v1.schema.json exactly.

Mapping rules:
- verdict comes straight from the lane (one-sided). If the lane produced no verdict (pure escalation), set verdict=UNCHECKABLE.
- action/final_status are policy, decided here, not by the checker:
    RULED_OUT_WRONG  -> action=reject (unless a repair lane applies; repair is Prompt 4)  -> final_status=rejected
    NOT_RULED_OUT    -> action=accept -> final_status=accepted
    UNCHECKABLE      -> action=escalate -> final_status=escalated
  high risk / unknown task -> action=escalate regardless.
- input_hash = sha256 of canonical-json(payload). decision_id = f"{input_hash[:16]}-{repair_attempt}".
- Embed the controller's record dict under validator_record.
- latency_ms measured around the route_decide call.
- strict=True: if final_status in {escalated} or verdict==UNCHECKABLE, the decision is still returned but is_blocking()=True for the CLI to exit non-zero.

Add tests/test_harness_core.py with one fixture per lane (arithmetic, json_schema, python_code, extraction, long_context_qa, retrieval) asserting each returns a schema-valid HarnessDecision (validate against the JSON Schema file). This 6-row matrix is the WP1 done-gate.
```

### Prompt 2 — CLI

```
Implement src/routemap_harness/__main__.py with main() and subcommands, runnable as:
    PYTHONPATH=src python -m routemap_harness <cmd>

Subcommands:
- check   --task <task_type> [--schema FILE] [--strict] [--risk low|high]  reads payload from --input FILE or stdin, prints the HarnessDecision as JSON, appends to the audit JSONL, exits non-zero in --strict when the decision is blocking.
- repair  --decision-id ID  (wired in Prompt 4; stub now)
- route   --passage FILE --question STR [--router element|token]  prints kept vs cheap tokens + recall guard.
- summarize --audit data/outputs/audit.jsonl  (wired in Prompt 6; stub now)
- validate-config  validates schemas/harness_decision_v1.schema.json loads, every task_type maps to a lane or explicit escalation, and the lane registry has no unmapped types; exit non-zero on any gap.

Keep all logic in core.py/policy.py; the CLI only parses args and prints. Add tests/test_cli.py covering `check` on a JSON-schema example and `validate-config` passing.
```

### Prompt 3 — Repair loop (migrate `dr_repair_wrapper_v1`)

```
Implement repair in src/routemap_harness/policy.py and wire `routemap-harness repair` + an in-loop repair path in core.harness_check.

Reuse dr_repair_wrapper_v1.build_repair_prompt for the per-lane prompt text (arithmetic, json_schema, python_code). Do not rewrite those prompts; import them. If you must adapt, move the function into policy.py and leave dr_repair_wrapper_v1 importing from there (single source of truth).

Behavior:
- repair(decision, original_payload, model_fn, *, max_retries=2) loops: build lane-specific prompt -> call model_fn -> re-run harness_check on the new output -> stop when verdict==NOT_RULED_OUT or max_retries hit.
- Each attempt emits its own audit record with incremented repair_attempt, linked by the same input_hash family; action=repair, final_status=repaired on success else escalated.
- Arithmetic: if still RULED_OUT_WRONG after retries, escalate to full_compute and record the exact result using the EXISTING exact path — routemap_digital.parse_expression(expr) -> expr_spec, then routemap_bench.tasks.exact_value_feasible(expr_spec) (or compute_ground_truth). Do NOT write a new evaluator and never eval() the expression. Never accept a ruled-out answer.
- Anti-hallucination guard: after any repair, re-run FULL validation; if a field that was valid before is now invalid, reject the repair and escalate.
- false_accepts counter: increment only if a known-wrong output (gold) reaches final_status=accepted; must stay 0 on the gold suite.

Tests: tests/test_repair.py with a stub model_fn (no network) — one JSON-schema failure that repairs to valid, one arithmetic that stays wrong and escalates to exact compute, and the anti-hallucination case.
```

### Prompt 4 — Escalation policy

```
Centralize escalation in src/routemap_harness/policy.py as decide_escalation(decision) -> escalation_target in {full_compute, deterministic_tool, stronger_model, human_review}.

Rules (high to low priority):
- risk==high or task_type==unknown -> human_review (or full_compute if a deterministic tool covers the lane).
- arithmetic RULED_OUT_WRONG after repair -> deterministic exact compute (full_compute).
- UNCHECKABLE after extraction/code -> stronger_model if a model_fn is configured else human_review.
- long_context route guard weak -> full_compute (full context).
No cheap path may pass without the audit record naming the validator/guard that justified it (no silent prune). Add an assertion + test that every accept/repair/prune decision has a non-empty validator OR an explicit escalation_target.

Tests: tests/test_escalation.py covering each branch.
```

### Prompt 5 — Audit store + summarizer + schema enforcement

```
Implement src/routemap_harness/audit_store.py.

- append(decision, path="data/outputs/audit.jsonl"): validate the record against schemas/harness_decision_v1.schema.json (raise on invalid) then append one JSON line. 100% of emitted records must be schema-valid.
- summarize(path) -> dict and a Markdown table: counts by task_type, route_family, verdict, action, final_status; repair_success rate; escalation rate; false_accepts (must be 0 on gold); latency p50/p95 from latency_ms.
- Wire `routemap-harness summarize --audit FILE` to print the table.
- Reconcile schemas: the canonical record embeds the lane record under validator_record. Document the crosswalk from route_decision_v1 / validator_audit_v1 -> harness_decision_v1 in docs/AUDIT_SCHEMA.md.

Tests: tests/test_audit.py — emit one decision per final_status, assert all schema-valid, assert summarize returns correct counts and 0 false_accepts.
```

### Prompt 6 — Gold suite + evidence wiring (the "zero false accepts" gate)

```
Create a locked gold fixture set under data/harness_gold/ : for each lane, a handful of inputs with known-correct and known-WRONG outputs and a ground-truth label. Include a checksum file (sha256 manifest) so the set is frozen, mirroring src/blind/.

Add tests/test_harness_gold.py: run harness_check (+ repair where applicable) over the gold set and assert false_accepts == 0 and false_positive_rate == 0.000 in the sound lanes. This test is the enforcement behind the acceptance checklist.

Wire two new steps into run_evidence.py STEPS:
  ("pytest: harness core+gold", [... "tests/test_harness_gold.py" ...], "0 false accepts; FP 0.000"),
  ("demo: harness CLI check", [python -m routemap_harness check ...], "schema-valid decision + audit line").
Update EVIDENCE_PACK.md with the harness rows.
```

### Prompt 7 — Model runner adapters (`model_fn` contract) [roadmap WP9]

```
Implement src/routemap_harness/adapters.py defining the model_fn contract and stub adapters, inspired by the OpenClaw provider/model/runtime split — copy the separation, not a gateway.

Contract:
  model_fn(prompt: str, *, model_ref: str, runtime: str="ollama", auth_mode: str="local", timeout: int=60, strict_model: bool=False, fallbacks: list[str]|None=None) -> str

Adapters (each isolated, optional deps documented separately):
- ollama_adapter (local; reuse the pattern in dr_repair_wrapper_v1's ollama worker) — the always-supported deterministic baseline.
- openai_api_adapter (API key) and anthropic_api_adapter (API key) — real but gated behind env vars; skip cleanly if unset.
- CLI/OAuth runtimes (codex, claude-cli, gemini-cli): leave as clearly-marked experimental stubs, disabled by default; never bypass provider terms.

Every model call records provider, model_ref, runtime, auth_mode, fallback_used, latency, and tokens/cost-if-available into the decision (the optional audit fields). strict_model=True fails visibly instead of falling back. Pin provider per run_id/session_id so benchmarks are reproducible.

Tests: tests/test_adapters.py with the ollama adapter mocked (no network) verifying the contract shape, audit fields, and that strict_model raises instead of falling back.
```

### Prompt 8 — FastAPI service [roadmap WP3]

```
Add src/routemap_harness/api.py: a FastAPI app that imports core.harness_check / policy.repair / audit_store and exposes:
  POST /check   {task, model, output, spec}        -> HarnessDecision JSON
  POST /repair  {decision_id, model_ref?}          -> repair decision JSON
  GET  /audit/{decision_id}                          -> stored record
The route handlers contain NO validation logic — they only call core functions. Depends on requirements-api.txt (keep core numpy-only). Run: PYTHONPATH=src uvicorn routemap_harness.api:app.
Tests: tests/test_api.py using FastAPI TestClient for /check on a JSON example and /repair stub (skip if fastapi not installed).
```

### Prompt 9 — Demo pack + acceptance sweep [roadmap WP8 + §18]

```
Create runnable demos that write a summary with one command:
- examples/json_tool_call/, examples/arithmetic/, examples/extraction/, examples/long_context/ with sample inputs.
- scripts/run_demo_pack.py: runs check (+repair where relevant) over each demo, writes EVIDENCE/HARNESS_RESULTS.md (failures caught, repairs, escalations, audit completeness, latency p50/p95).
- scripts/run_model_matrix.py: same fixed prompts through ollama (local) + one API adapter if env is set, all validated by the SAME harness.

Then run the §18 acceptance checklist as an automated check (scripts/check_acceptance.py) and fix any gap:
clean checkout installs with requirements-dev.txt; check works for all lanes; every decision emits schema-valid JSONL; repair fixes >=1 JSON class and logs the rest; arithmetic wrong answers ruled out/escalated with 0 false accepts; unknown/high-risk escalates by default; run_evidence.py includes harness tests; README/EVIDENCE_PACK/report agree on defaults (element) and headline numbers; no wording claims correctness certification.
```

---

## After the agents run — your verification loop

1. `PYTHONPATH=src python -m pytest -q` (all green, harness tests included).
2. `PYTHONPATH=src python run_evidence.py` → check `EVIDENCE/RESULTS.md` shows the two new harness rows passing.
3. `PYTHONPATH=src python -m routemap_harness validate-config` exits 0.
4. `git diff --check` and a read of `EVIDENCE/HARNESS_RESULTS.md` for the 0-false-accepts line before committing.
