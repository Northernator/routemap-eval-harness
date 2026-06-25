# RouteMap Lab Mode — VS Code / Codex Prompt Sheet

Paste-ready specs to implement `ROADMAP_LAB_MODE.md`. Built for the Codex paste-spec loop.

## How to use

1. Open a Codex session in VS Code at the repo root.
2. Paste **SHARED CONTEXT** (below) once at the start of the session.
3. Then paste **one slice at a time, in order**. Each slice is self-contained.
4. After each slice, run the gates (in SHARED CONTEXT) and commit before moving on.
5. Slices are ordered Lab Mode → flagship lanes → diagnostics → prep/export → agent. Dependencies are noted per slice.

Commit convention: `lab-mode: slice N <name>` (one commit per slice).

---

## SHARED CONTEXT (paste once)

~~~text
You are working in the RouteMap harness. Repo working dir for ALL commands:

  routemap_eval_harness/routemap_eval_harness/

Python package source is under src/ ; tests import it with sys.path.insert(0, ".../src").
The web UI is a SINGLE vanilla-JS file: src/routemap_harness/web/app.html (no build step, no framework, no npm).
The HTTP surface is FastAPI in src/routemap_harness/api.py.

RUN THE SERVER (Windows PowerShell):
  $env:PYTHONPATH="src"; python -m uvicorn routemap_harness.api:app --reload --port 8000
  # then open http://127.0.0.1:8000/

GATES — a slice is DONE only when all pass, run from routemap_eval_harness/routemap_eval_harness/:
  python -m pytest -q
  python run_evidence.py        # must complete clean; add a STEPS entry for any new test file
  git diff --check              # no whitespace errors
Do not add a runtime dependency beyond requirements-api.txt (fastapi, uvicorn, pydantic) unless the slice says so.
Tests already depend on httpx and jsonschema (dev).

EXISTING CODE TO REUSE (do NOT reinvent):
- routemap_token.route_passage(passage, question="", *, router_mode="element", threshold=0.5)
    -> list of {token, route_action ("keep"|"cheap"), route_score}
- routemap_token.routers._score_sample(sample, idf_map, threshold, mode="element")
    -> rich rows incl. static_class, route_score, route_action,
       context_features {element, query_overlap, codon_value, mode}
- routemap_token.bench.TokenQASample(sample_id, context, question, answer, evidence, needed_phrases=())
    # route_passage builds it positionally: TokenQASample("passage", passage, question or "", "", "", ())
- routemap_token.prior.build_idf(list_of_texts)
- routemap_token.elements.classify_element(token), ELEMENT_WEIGHT
- routemap_token.routers.ELEMENT_ALWAYS == {"NEGATION","CODE","CITATION","INSTRUCT","RISK"}  (protected)
- routemap_harness.core.harness_check(payload, *, budget="balanced", risk="low",
       router_mode=None, strict=False, model_fn=None, max_retries=2) -> HarnessDecision
- routemap_harness.core.route_tokens(passage, question, *, router="element")
- routemap_harness.adapters.model_fn(prompt, *, model_ref, runtime, auth_mode,
       timeout=60, strict_model=False, fallbacks=None) -> ModelResponse(str)
       ModelResponse has .metadata (ModelCallMetadata: provider, model_ref, runtime, auth_mode,
       fallback_used, latency_ms, tokens, cost_usd, run_id, session_id)
- routemap_harness.adapters.metadata_dict(response) -> dict ; ModelAdapterUnavailable, ModelAdapterError
- routemap_harness.audit_store.append/tail/get_record/summarize/summarize_records
- routemap_controller.route_decide(input, task=None, *, budget, risk, router_mode=None)
- routemap_controller.classify.classify(input, task_hint=None) -> TaskEnvelope ; classify.TASK_TYPES (set)
- routemap_validators.check_output(raw, task_type, spec=None, *, object_id=None, model=None) -> Decision
- routemap_validators.verdicts.Verdict (RULED_OUT_WRONG, NOT_RULED_OUT, UNCHECKABLE)
- api.py helpers: _run_payload, _optimize_prompt, _api_decision, _audit_path, _auth_mode

HARD CONSTRAINTS (every slice):
1. No-leak: routing/visualizing NEVER reads a gold answer or evidence label. Only inference-time
   signals (element, query overlap, score, idf).
2. The decision schema is FROZEN: schemas/harness_decision_v1.schema.json is additionalProperties:false.
   Never add fields to the HarnessDecision record. Per-run I/O (prompt, model_output, etc.) goes in the
   run store (Slice 7) or inside validator_record (an object field that is already allowed).
3. Adding a new task_type/lane requires editing ALL of these in sync:
     - src/routemap_controller/classify.py  (TASK_TYPES + a signature rule)
     - src/routemap_controller/controller.py (route_decide branch + a _plan call)
     - src/routemap_harness/core.py          (TASK_TYPES, LANE_REGISTRY, and ROUTE_FAMILY_BY_CONTROLLER if a new family)
     - schemas/harness_decision_v1.schema.json (task_type enum, and route_family enum if a new family)
     - src/routemap_validators/ (a checker, if the lane verifies output)
4. Determinism: temperature 0, fixed seeds. UI persists state in localStorage (existing pattern).
5. TEST PATTERNS already in this repo (mirror them exactly):
     - from fastapi.testclient import TestClient ; client = TestClient(api.app)
     - isolate audit: api.app.state.audit_path = str(tmp_path / "audit.jsonl")
     - stub the model: monkeypatch.setattr(api, "model_fn", lambda prompt, **kw: "...")
     - validate decisions with jsonschema Draft202012Validator against the schema file
     - API verdicts are returned LOWERCASED via _api_decision (e.g. "ruled_out_wrong")
Keep every change additive and backward compatible. Report a unified diff per file.
~~~

---

## Slice 1 — `POST /route` + Before/After token visualizer  (Phase 1A)

Goal: make the token optimizer visible. Show the input token-by-token (kept / cheap / protected / question-overlap) and the compressed prompt that would be sent.

~~~text
SLICE 1 — /route endpoint + token visualizer. Shared context applies.

BACKEND
1. In src/routemap_token/routers.py add and export:
     def route_passage_detail(passage, question="", *, router_mode="element", threshold=0.5)
   Reuse the existing scoring path (build TokenQASample + build_idf, then _score_sample for the
   non-"token" modes, or score_sample for "token"). Return a list of rows:
     {token, route_action, route_score, element, query_overlap, protected}
   where element = context_features["element"], query_overlap = context_features["query_overlap"],
   protected = element in ELEMENT_ALWAYS. Add to __all__ and re-export from routemap_token/__init__.py.
   No-leak: signature takes only passage + question (no gold).

2. In src/routemap_harness/api.py add:
     @app.post("/route")
     def route(body): ...
   Input: {passage, question?, router_mode?}. Call route_passage_detail. Respond:
     {router_mode, tokens, kept, cheap, reduction (1 - kept/tokens),
      compressed_prompt (" ".join kept tokens), rows: [ ...as above... ]}
   No audit write (this is a preview endpoint).

FRONTEND (src/routemap_harness/web/app.html)
3. Refactor the 2-button .segmented tab bar into an N-tab bar (keep Check, Chat). Add a "Lab" tab.
4. Lab panel: a passage textarea, a question input, a "route" button, a legend, a rendered token
   stream, and a "prompt sent" block showing compressed_prompt with a "compressed X -> Y (-Z%)" chip.
   Render each row as a <span> with a title=element. Colors (reuse CSS vars / add minimal classes):
     - cheap            -> grey (var(--muted))
     - keep + protected -> red border (var(--bad))      [cannot drop]
     - keep + query_overlap (not protected) -> yellow (var(--warn))
     - keep (other)     -> green (var(--good))
   Persist last passage/question in localStorage (keys routemap.lab.passage / .question), matching the
   existing localStorage pattern. Use the existing escapeHtml + request() helpers.

TESTS
5. tests/test_api.py: add test_route_endpoint_highlights_tokens — POST /route with a long passage that
   contains a negation ("not") and filler ("the of and to") and a content sentence. Assert 200; rows
   non-empty; at least one route_action=="cheap" and one "keep"; the "not" token row has protected True;
   compressed_prompt word-set is a subset of the passage word-set.
6. rt_test_elements.py: add test_route_passage_detail_is_deterministic_and_noleak — same input twice gives
   identical rows; assert route_passage_detail has no parameter named answer/evidence/needed.
7. tests/test_web.py: extend test_app_page_served to assert the served HTML contains a Lab tab id.
8. run_evidence.py STEPS: add ("pytest: api+web", [sys.executable,"-m","pytest","tests/test_api.py","tests/test_web.py","-q"], "route endpoint + web surface").

DONE WHEN: all gates pass; live server shows highlighted tokens + compressed prompt for a pasted passage.
~~~

---

## Slice 2 — Run cockpit tab  (Phase 1B) — depends on Slice 1

Goal: turn the Chat tab into a full run cockpit that shows the whole pipeline for one run.

~~~text
SLICE 2 — Run cockpit. Shared context applies. /run already returns every field below.

FRONTEND ONLY (src/routemap_harness/web/app.html)
1. Rename the "Chat" tab to "Run" (keep the same panel + thread). Keep the compress-context toggle.
2. After each /run, render a collapsible "run detail" card under the assistant bubble showing:
     - prompt           (body.prompt)
     - prompt_sent      (body.prompt_sent) with the existing compression chip when body.compressed
     - model_output     (body.model_output)
     - final_output     (body.final_output)  [highlight when != model_output]
     - decision kv      verdict / action / final_status / validator / latency_ms (reuse renderDecision style)
     - repair attempts  render body.repair_attempts (array) as a small table: attempt #, verdict, action
     - tokens           "before -> after (-reduction%)" from tokens_before/tokens_after/reduction
     - audit_id         body.audit_id (plain text now; Slice 7 turns it into a Replay button)
3. Keep it vanilla JS + existing CSS vars. Persist the last prompt in localStorage (routemap.run.prompt).

TESTS
4. tests/test_web.py: extend the served-page test to assert the HTML contains a Run tab id and a
   run-detail container id.
5. tests/test_api.py: add test_run_returns_pipeline_fields — monkeypatch api.model_fn to return a fixed
   string; POST /run with task_hint "arithmetic" and prompt "2 + 2"; assert body has keys
   prompt, prompt_sent, model_output, final_output, decision, repair_attempts, tokens_before,
   tokens_after, reduction, audit_id.
6. run_evidence.py: covered by the Slice 1 api+web STEPS entry (no new entry needed).

DONE WHEN: gates pass; a single run shows input compression, raw vs final output, verdict, repairs, tokens, latency in one panel.
~~~

---

## Slice 3 — `POST /compare` + Compare tab  (Phase 1C) — depends on Slice 2

Goal: the AI-lab demo — one prompt, many models, side by side.

~~~text
SLICE 3 — multi-model compare. Shared context applies.

BACKEND (src/routemap_harness/api.py)
1. Refactor the body of run() into a reusable helper:
     def _run_once(body, *, runtime, model_ref) -> dict
   returning exactly the dict /run returns today. Make /run call _run_once. (Pure refactor; keep /run
   response identical so existing tests pass.)
2. Add:
     @app.post("/compare")
     def compare(body): ...
   Input: {prompt, models: [{runtime, model_ref}], compress_context?, strict?, task_hint?, spec?}.
   For each model: call _run_once with a per-model body. Catch ModelAdapterUnavailable / ModelAdapterError
   per model and record {available:false, error:str} instead of failing the whole request.
   Respond: {prompt, results: [ { runtime, model_ref, available, model_output, final_output,
     decision, repair_attempts, tokens_before, tokens_after, reduction, latency_ms, cost_usd, error? } ]}.
   Pull latency_ms/cost_usd from the decision and/or model metadata that _run_once already has access to.

FRONTEND (app.html)
3. Add a "Compare" tab: prompt textarea, a checkbox list of models built from GET /models (only
   selectable when available), a "compare" button, and a results table with columns:
     Model | Output | Verdict | Repair | Tokens (before->after) | Cost | Time(ms)
   Color the verdict cell (reuse verdictClass). Show the error string for unavailable models.

TESTS (tests/test_api.py)
4. test_compare_runs_each_model — monkeypatch api.model_fn to echo its model_ref kwarg; POST /compare with
   two models; assert two results, each available True, each decision present.
5. test_compare_isolates_model_failure — monkeypatch api.model_fn to raise ModelAdapterUnavailable for one
   model_ref and succeed for another; assert the failing one has available False + error, the other ok,
   and status_code stays 200.

DONE WHEN: gates pass; Compare tab shows one prompt across selected models with verdict/tokens/cost/time.
~~~

---

## Slice 4 — Tool-call firewall lane  (Phase 2A)

Goal: validate/repair/reject a proposed tool call's JSON before it could ever execute.

~~~text
SLICE 4 — tool_call lane. Shared context applies. Follow constraint #3 (edit all sync points).

NEW TASK TYPE: "tool_call"  (route_family: reuse "sound_checker" -> no schema route_family change)
1. schemas/harness_decision_v1.schema.json: add "tool_call" to the task_type enum.
2. src/routemap_harness/core.py: add "tool_call" to TASK_TYPES and LANE_REGISTRY ("tool_call": "sound_checker").
3. src/routemap_controller/classify.py: add "tool_call" to TASK_TYPES; add a signature rule:
   dict with "tool_call" key, or {"name"/"tool" and "arguments"/"args"} -> TaskEnvelope("tool_call", ...).
4. src/routemap_validators: add a checker module tool_call_firewall.py with:
     def check_tool_call(call, *, schema=None, allowed_tools=None) -> Decision-like result
   Checks (each a named check; first failure -> RULED_OUT_WRONG with a clear reason):
     - arguments parse as JSON object
     - if schema given: required fields present, types match (reuse the existing json_schema checker path)
     - tool name in allowed_tools (when provided); else RULED_OUT_WRONG "disallowed tool"
     - safety rules: reject path args containing ".." or absolute/system paths; reject impossible numbers
       (NaN/inf, negative where the schema minimum is 0); reject invalid ISO dates in date-typed fields.
   If all pass -> NOT_RULED_OUT (executable). Wire it into routemap_validators.check_output for
   task_type=="tool_call", and into controller.route_decide via a _tool_call(...) branch using
   route_family "sound_checker".
5. core.py / api.py: tool_call repairs like json_schema (verdict RULED_OUT_WRONG + model_fn -> repair).

FRONTEND (app.html)
6. In the Check tab task dropdown add option "tool_call". When selected, the schema box doubles as the
   tool-call schema and add an optional "allowed tools" comma input passed as body.allowed_tools.
   Show the failing check name + reason in the decision panel.

TESTS
7. rv_test_validator_package.py: add cases — valid call passes; missing required field -> RULED_OUT_WRONG;
   path arg "../etc/passwd" -> RULED_OUT_WRONG; tool not in allowed_tools -> RULED_OUT_WRONG; invalid date
   -> RULED_OUT_WRONG. Assert reasons are specific.
8. tests/test_harness_core.py: add a "tool_call" param to FIXTURES so the decision stays schema-valid.
9. tests/test_api.py: test_check_tool_call_rejects_unsafe_path via POST /check task "tool_call".
10. run_evidence.py STEPS: add ("pytest: tool-call firewall", [sys.executable,"-m","pytest","rv_test_validator_package.py","-q"], "tool-call firewall checks") OR extend the existing validators step note.

DONE WHEN: gates pass; an invalid/unsafe tool call is rejected with a specific reason; a valid one passes; a repairable one is repaired.
~~~

---

## Slice 5 — Citation / source grounding lane  (Phase 2B)

Goal: catch unsupported claims in RAG/document answers. Simple checks first, no NLI.

~~~text
SLICE 5 — grounded_qa lane. Shared context applies. NEW route_family this time.

NEW TASK TYPE: "grounded_qa" + NEW route_family: "grounding"
1. schemas/harness_decision_v1.schema.json: add "grounded_qa" to task_type enum AND "grounding" to
   route_family enum.
2. src/routemap_harness/core.py: TASK_TYPES += "grounded_qa"; LANE_REGISTRY["grounded_qa"]="grounding";
   ROUTE_FAMILY_BY_CONTROLLER["grounding"]="grounding".
3. src/routemap_controller/classify.py: add "grounded_qa"; signature rule: dict with "answer" and
   "source" (or "sources") -> TaskEnvelope("grounded_qa", ...).
4. src/routemap_validators: add grounding.py with
     def check_grounding(answer, source, *, require_citation=True) -> result
   Reuse routemap_token.elements.classify_element to pull ENTITY / NUMBER / DATE tokens from the answer.
   Checks (collect ALL, verdict RULED_OUT_WRONG if any required check fails):
     - every ENTITY token in the answer appears in source text (case-insensitive)
     - every NUMBER / DATE token in the answer appears in source
     - a source id / citation marker is present in the answer when require_citation ([n] or a source key)
     - the evidence overlap is non-trivial (>=1 content token shared)
   Unsupported -> RULED_OUT_WRONG with reason listing the missing items; fully grounded -> NOT_RULED_OUT;
   if answer has no checkable entities/numbers -> UNCHECKABLE (escalate). Wire into check_output and a
   controller _grounded_qa(...) branch (route_family "grounding"), validator name "grounding_guard".

FRONTEND (app.html)
5. Add "grounded_qa" to the Check task dropdown. Add a "source" textarea (shown for this task) sent as
   body.source. Decision panel lists the unsupported items.

TESTS
6. New rt_test_grounding.py (root, like the other r*_test_*.py): grounded answer passes; an answer with an
   entity/number absent from source -> RULED_OUT_WRONG naming it; answer with no citation and
   require_citation -> RULED_OUT_WRONG; answer with no checkable claims -> UNCHECKABLE. Assert no-leak
   (function reads only answer + source).
7. tests/test_harness_core.py: add a "grounded_qa" FIXTURE param (schema-valid decision).
8. run_evidence.py STEPS: add ("pytest: grounding", [sys.executable,"-m","pytest","rt_test_grounding.py","-q"], "citation/source grounding").

DONE WHEN: gates pass; unsupported claim escalates/rejects with named missing items; grounded claim passes.
~~~

---

## Slice 6 — Failure Genome dashboard  (Phase 3A) — depends on Slices 4–5 for richer data

Goal: aggregate failures instead of showing one decision at a time. Data already exists in audit_store.

~~~text
SLICE 6 — Failure Genome. Shared context applies. summarize_records already computes the metrics.

BACKEND (src/routemap_harness/audit_store.py + api.py)
1. In audit_store.py extend summarize_records to also return a "by_model" breakdown: for each model,
   the same counts (task_type, verdict, action, final_status) + false_accepts + repair_success_rate.
   Keep the existing top-level keys unchanged (additive only).
2. In api.py add:
     @app.get("/summary")
     def summary(): return audit_store.summarize(_audit_path())
   (summarize already attaches "markdown"; the by_model block rides along.)

FRONTEND (app.html)
3. Add a "Dashboard" tab. On open, GET /summary and render:
     - KPI row: total, acceptance_rate, escalation_rate, repair_success_rate, false_accepts,
       latency p50/p95.
     - "Failures by type" from counts.verdict / counts.action (e.g. RULED_OUT_WRONG, escalate counts).
     - "By model" table from by_model.
   Plain HTML tables + the existing CSS. No chart library (parking-lot: heavy polish).

TESTS (tests/test_api.py / tests/test_audit.py)
4. test_summary_endpoint_aggregates — write a few decisions via /check and /run (monkeypatched model),
   GET /summary, assert total matches and counts/by_model are present.
5. tests/test_audit.py: add test_summarize_records_has_by_model over a small synthetic record list.
6. run_evidence.py STEPS: add tests/test_audit.py to an api+audit step (or extend the api+web step list).

DONE WHEN: gates pass; Dashboard shows failure counts overall and per model from the live audit log.
~~~

---

## Slice 7 — Run store + Replay mode  (Phase 3B) — depends on Slice 2

Goal: replay any decision end to end. Needs a run store because the decision schema is frozen.

~~~text
SLICE 7 — run store + replay. Shared context applies. Do NOT add fields to the decision schema.

BACKEND
1. New module src/routemap_harness/run_store.py (mirror audit_store.py style):
     DEFAULT_RUNS = ROOT / "data" / "outputs" / "runs.jsonl"
     def append_run(record, path=DEFAULT_RUNS) -> dict   # record keyed by decision_id
     def get_run(decision_id, path=DEFAULT_RUNS) -> dict | None
   Run record shape:
     {decision_id, timestamp, prompt, prompt_sent, model_output, final_output, repair_attempts,
      compression {compressed, tokens_before, tokens_after, reduction, route_note},
      model {runtime, model_ref, auth_mode, latency_ms, cost_usd, tokens}}  # from metadata_dict
   No schema validation here (free-form run log), but keep it JSONL + sorted keys.
2. api.py: in _run_once, after building the response, also append_run(...) with a runs path from
   app.state (add _runs_path() like _audit_path(), default run_store.DEFAULT_RUNS). Pull model metadata
   via adapters.metadata_dict(model_output).
3. api.py: add
     @app.get("/replay/{decision_id}")
     def replay(decision_id):
   Return {decision: audit_store.get_record(id), run: run_store.get_run(id)} ; 404 if both missing.

FRONTEND (app.html)
4. In the Run cockpit and the recent-decisions table, turn audit_id / each row into a "Replay" button.
   On click GET /replay/{id} and show a modal/panel with: input prompt, model, prompt sent, compression,
   raw output, validators (decision.validator + reason), repair prompt/attempts, final output, raw audit
   record (pretty JSON). Reuse escapeHtml; vanilla modal.

TESTS (tests/test_api.py)
5. test_run_persists_run_store — monkeypatch model; POST /run; GET /replay/{audit_id}; assert run.prompt,
   run.model_output, run.compression present and decision present.
6. test_replay_404_for_unknown_id.
7. new tests/test_run_store.py: append_run then get_run round-trips by decision_id.
8. run_evidence.py STEPS: add ("pytest: run store + replay", [sys.executable,"-m","pytest","tests/test_run_store.py","-q"], "replay run log").

DONE WHEN: gates pass; clicking a decision replays the full run; decision schema unchanged (run I/O lives in runs.jsonl).
~~~

---

## Slice 8 — Prompt optimizer (structured prep)  (Phase 4A) — depends on Slice 2

Goal: rewrite a loose prompt into a structured task spec before the model sees it.

~~~text
SLICE 8 — prompt optimizer. Shared context applies.

BACKEND
1. New module src/routemap_prompt/__init__.py + optimize.py:
     def optimize_prompt(prompt, *, task_hint=None) -> {structured, preserved, note}
   Use routemap_token.elements.classify_element over the prompt tokens to extract: INSTRUCT verbs,
   ENTITY, NUMBER, DATE, NEGATION, CITATION, THRESHOLD, RISK. Emit a structured prompt string:
     "Task: <instruct verbs / task_hint>.
      Preserve exactly: <numbers, dates, negations, entities, citations found>.
      Constraints: <negations/thresholds/risk terms>.
      Return: <format hint if any, else 'a direct, checkable answer'>."
   preserved = the literal tokens that must survive. No-leak: only the prompt is read.
2. api.py: in _run_once, when body.optimize_prompt is true, replace the prompt with structured BEFORE
   _optimize_prompt compression, and add {optimized:true, optimized_prompt, preserved} to the response.
   (optimize = rewrite; compress = drop filler; they compose, optimize first.)

FRONTEND (app.html)
3. Run tab: add a "structure prompt" toggle (localStorage routemap.optimize). When on, show the
   optimized_prompt and the preserved chips in the run detail card.

TESTS
4. new tests/test_prompt_optimizer.py: a loose prompt with a number, a date, and "not" yields a structured
   string containing those literals in "Preserve exactly"; deterministic; no-leak.
5. tests/test_api.py: test_run_optimizes_prompt_when_enabled — body.optimize_prompt true -> response has
   optimized true and optimized_prompt non-empty.
6. run_evidence.py STEPS: add ("pytest: prompt optimizer", [sys.executable,"-m","pytest","tests/test_prompt_optimizer.py","-q"], "structured prompt prep").

DONE WHEN: gates pass; toggling "structure prompt" rewrites the prompt and preserves numbers/dates/negations/entities.
~~~

---

## Slice 9 — RouteMap coverage scorecard  (Phase 4B) — depends on Slices 4–5

Goal: an honest coverage scorecard (never a fake correctness probability).

~~~text
SLICE 9 — coverage scorecard. Shared context applies. NEVER output a "% correct".

BACKEND
1. New src/routemap_harness/scorecard.py:
     def scorecard(decision_dict, *, run=None) -> dict
   Compute, from the decision (+ validator_record, + optional run):
     - validation_coverage: fraction of the output that was covered by a checkable route
       (checked vs total claims/fields the validator saw; for json_schema use checks count;
        for grounded_qa use grounded vs total claims; else 1.0 if a verdict was produced, 0.0 if UNCHECKABLE)
     - hard_failures: count of RULED_OUT_WRONG checks
     - unchecked_claims: claims with no applicable checker
     - repair_attempts, escalation_required (bool), input_compression (from validator_record), 
       source_grounding ("full"|"partial"|"none"|"n/a")
   Return plain numbers + a one-line honest summary like
     "72% of this output was covered by checkable routes; 0 hard failures; 1 repair."
2. api.py: attach scorecard(...) to /check and /run responses under "scorecard".

FRONTEND (app.html)
3. Render a scorecard card in Check + Run results: coverage as "X% covered by checkable routes" (bar),
   hard failures, unchecked claims, repairs, escalation, compression, grounding. Explicit caption:
   "Coverage, not a correctness score."

TESTS
4. new tests/test_scorecard.py: a json_schema decision yields coverage in [0,1] and hard_failures matching
   the failing checks; an UNCHECKABLE decision yields coverage 0.0 and escalation_required True; the
   summary string never contains the word "correct".
5. tests/test_api.py: assert /check response includes a scorecard block with the expected keys.
6. run_evidence.py STEPS: add ("pytest: scorecard", [sys.executable,"-m","pytest","tests/test_scorecard.py","-q"], "honest coverage scorecard").

DONE WHEN: gates pass; every result shows a coverage scorecard; no output ever claims a correctness percentage.
~~~

---

## Slice 10 — Failures → training JSONL export  (Phase 4C) — depends on Slice 7

Goal: export failures as fine-tuning-ready JSONL from the run store + audit.

~~~text
SLICE 10 — training export. Shared context applies.

BACKEND
1. src/routemap_harness/run_store.py: add
     def export_failures(audit_path, runs_path) -> list[dict]
   Join audit records to run records by decision_id; keep records where final_status in
   {"rejected","escalated","repaired"} or verdict=="RULED_OUT_WRONG". Emit rows:
     {prompt, model_output, failure_type (task_type + ":" + first failing check or verdict),
      validator_reason (decision.reason), repair_prompt (from run.repair_attempts if any),
      corrected_output (run.final_output when != model_output), final_status}
2. api.py:
     @app.get("/export/failures")
     def export_failures_endpoint():
   Return the rows as a JSONL string with media_type "application/x-ndjson" (use fastapi Response), so the
   browser downloads it. Reuse _audit_path()/_runs_path().

FRONTEND (app.html)
3. Dashboard tab: an "Export failures (JSONL)" button that GETs /export/failures and triggers a client
   download (Blob + a tags). Show the row count.

TESTS
4. tests/test_run_store.py: add test_export_failures_joins_audit_and_runs — seed one failing run, assert one
   exported row with the expected keys and failure_type.
5. tests/test_api.py: test_export_failures_returns_ndjson — status 200, content-type ndjson, body lines parse as JSON.
6. run_evidence.py STEPS: covered by the Slice 7 run-store step (extend its note) or add an export step.

DONE WHEN: gates pass; the Dashboard exports a JSONL of failures with prompt/output/failure_type/reason/repair/final_status.
~~~

---

## Slice 11 — Minimal agent control loop  (Phase 5, stretch) — depends on Slice 4

Goal: a small, bounded control loop. Ship minimal only; no autonomous orchestration.

~~~text
SLICE 11 — minimal agent loop. Shared context applies. Keep it BOUNDED (max 1 tool step).

BACKEND
1. New src/routemap_agent/__init__.py + loop.py:
     def run_agent(goal, tools, model_fn, *, max_steps=1) -> {steps, final, audit_ids}
   Loop, each step:
     a. ask model_fn for a plan (text) -> record
     b. ask model_fn for ONE tool call (JSON) -> harness_check task_type "tool_call" (reuse Slice 4);
        if RULED_OUT_WRONG -> repair once, else escalate and stop
     c. execute the tool only if NOT_RULED_OUT (tools is a dict name->callable; no network, no shell)
     d. harness_check the tool OUTPUT (json_schema or grounded_qa if a schema/source is supplied)
     e. produce a final answer; append every decision to the audit log.
   Hard caps: max_steps default 1; refuse tools not in the passed dict; never exec shell/network.
2. api.py: @app.post("/agent") -> run_agent with a small built-in safe tool registry (e.g. a pure
   calculator + a fixed lookup) for the demo. Returns steps + final + audit_ids.

FRONTEND (app.html)
3. Add an "Agent" tab: goal input, "run" button, and a step trace (plan, tool call + firewall verdict,
   tool output + check, final). Each step links to Replay (Slice 7).

TESTS (tests/test_agent.py)
4. test_agent_blocks_unsafe_tool_call — model proposes a disallowed/unsafe tool call -> loop escalates,
   tool not executed.
5. test_agent_happy_path — valid plan + valid tool call -> tool executes, output checked, final produced,
   audit_ids non-empty. Stub model_fn with scripted outputs (mirror the repair test's scripted model_fn).
6. run_evidence.py STEPS: add ("pytest: agent loop", [sys.executable,"-m","pytest","tests/test_agent.py","-q"], "bounded agent control loop").

DONE WHEN: gates pass; the Agent tab runs plan -> firewalled tool call -> output check -> final, and an unsafe call is blocked before execution.
~~~

---

## After all slices

- Update `ROADMAP_LAB_MODE.md` status as phases land.
- Consider a `serve` subcommand in `src/routemap_harness/__main__.py` (wrapping uvicorn) so the cockpit starts with `python -m routemap_harness serve` instead of the raw uvicorn line.
- Parking lot stays parked: RNS, matrix/KV, fine-tuning runs, heavy chart polish, more providers, full agent orchestration.
- Final sweep before a release tag: `python -m pytest -q && python run_evidence.py && git diff --check`.
