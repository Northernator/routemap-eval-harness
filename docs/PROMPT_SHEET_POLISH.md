# RouteMap Cockpit Polish — Codex Prompt Sheet

Paste-ready specs to polish the existing cockpit into an "AI reliability cockpit." No new theory lanes —
presentation and one small API fix only. Built for the Codex paste-spec loop.

## How to use
1. Paste **SHARED CONTEXT** once at the start of a Codex session.
2. Paste **one slice at a time, in order** (P1 → P4). Each is self-contained.
3. Run the gates after each, commit, then move on.

Commit convention: `polish: slice P<n> <name>`.

---

## SHARED CONTEXT (paste once)

~~~text
You are polishing the RouteMap cockpit. Repo working dir for ALL commands:

  routemap_eval_harness/routemap_eval_harness/

The UI is a SINGLE vanilla-JS file: src/routemap_harness/web/app.html (no framework, no build step).
The HTTP surface is FastAPI in src/routemap_harness/api.py. Start it: routemap-harness serve  (http://127.0.0.1:8000/).

GATES — a slice is done only when all pass, from routemap_eval_harness/routemap_eval_harness/:
  python -m pytest -q
  python run_evidence.py        # the api+web step covers tests/test_api.py + tests/test_web.py
  git diff --check
No new runtime dependency. Keep changes additive.

CURRENT UI STRUCTURE (src/routemap_harness/web/app.html):
- Six tabs via setMode(mode); modes are exactly: "check","run","compare","dashboard","agent","lab".
- A plain-language help line #tab-help sits under the header (set in setMode from a TAB_HELP map).
- Key JS helpers already defined (reuse them, do not duplicate):
    setMode(mode), escapeHtml(v), verdictClass(v)  // -> "verdict-<lower>"
    renderDecision(decision), renderAudit(records), replayButton(id), openReplay(id)
    renderScorecard(card), renderRunDetail(run), renderCompareResults(results), renderAgent(result)
    runKv(key, value, cls=""), compressionLabel(run), preservedChips(values)
    handleReplayClick(event)  // delegated on the run thread + audit table
- Element refs already declared near the top of <script>: modelSelect, taskSelect, outputField, specField,
    allowedToolsField, sourceField, strictField, checkForm, decisionEl, repairBtn, auditBody, chatForm,
    promptField, thread (#run-detail-container), labForm, labPassage, labQuestion, compareForm, agentForm, tabHelp.
- CSS custom properties: --good (green), --bad (red), --warn (amber), --accent (teal),
    --accent-2 (blue), --muted, --line, --panel, --text.

VERDICT TOKENS (technical; keep them in JSON/audit, relabel only for display in slice P2):
    RULED_OUT_WRONG, NOT_RULED_OUT, UNCHECKABLE.
    NOTE: /check returns the verdict UPPERCASE; /run's `decision.verdict` is lowercased by the API
    (_api_decision). verdictClass() already lowercases for CSS. Any new label helper must be case-insensitive.

/run RESPONSE FIELDS available to the UI (already returned today):
    prompt, prompt_sent, optimized, optimized_prompt, preserved[], model_output, final_output,
    decision { verdict, action, final_status, validator, reason, latency_ms, decision_id, model },
    repair_attempts[], compressed, tokens_before, tokens_after, reduction, route_note,
    audit_id, exact_correction, scorecard.

API (src/routemap_harness/api.py) facts for slice P4:
- Imports already present: model_fn, harness_check, repair (from .policy), scorecard, audit_store,
    HTTPException, ModelAdapterUnavailable, ModelAdapterError, DEFAULT_MODEL_REF.
- Helpers already present: _check_payload(body), _api_decision(decision), _audit_path(),
    _auth_mode(runtime), _with_model_record(decision, model), _exact_correction(payload, decision).
- policy.repair(decision, payload, model_fn, *, max_retries=2, audit_path=None) -> RepairResult
    RepairResult.final_decision (HarnessDecision), .attempts (list[HarnessDecision]), .to_dict().
    It calls model_fn with the adapter signature (prompt, model_ref=, runtime=, auth_mode=, ...),
    reading model_ref/runtime/auth_mode FROM the payload. policy.REPAIRABLE_TASKS =
    {"arithmetic","json_schema","tool_call","python_code"}; other task types come back escalated.

TEST PATTERNS (mirror exactly):
- from fastapi.testclient import TestClient ; client = TestClient(api.app)
- isolate audit: api.app.state.audit_path = str(tmp_path / "audit.jsonl")
- stub the model: monkeypatch.setattr(api, "model_fn", lambda prompt, **kw: "...")
- tests/test_web.py asserts STATIC strings in the served app.html (it greps response.text), so to test
    client-rendered JS, assert the function/marker text exists in the page source.

CONSTRAINTS:
- Slices P1–P3 touch ONLY app.html. Slice P4 touches api.py + app.html + tests/test_api.py.
- Plain-language labels are DISPLAY-ONLY: never change API responses, the audit JSONL, or the decision schema.
- Keep the raw-audit JSON block in the replay modal technical (do not relabel it).
Report a unified diff per file.
~~~

---

## Slice P1 — Run timeline (color-coded lifecycle)  [app.html only]

Goal: turn the flat Run-detail key/value list into a visible lifecycle so a run *reads* like a control system.

~~~text
SLICE P1 — run timeline. Shared context applies. Edit ONLY src/routemap_harness/web/app.html.

CSS (add near the .run-detail rules):
  .timeline { display: grid; gap: 8px; margin: 10px 0; }
  .timeline-step { display: grid; grid-template-columns: 14px minmax(0,1fr); gap: 10px;
    align-items: start; padding: 8px 10px; border: 1px solid var(--line);
    border-left: 3px solid var(--muted); border-radius: 8px; }
  .timeline-step .dot { width: 10px; height: 10px; border-radius: 999px; margin-top: 5px; background: var(--muted); }
  .timeline-step .step-title { font-weight: 700; }
  .timeline-step .step-detail { color: var(--muted); font-size: 0.86rem; overflow-wrap: anywhere; }
  .step-pass  { border-left-color: var(--good); }   .step-pass  .dot { background: var(--good); }
  .step-block { border-left-color: var(--bad); }    .step-block .dot { background: var(--bad); }
  .step-warn  { border-left-color: var(--warn); }   .step-warn  .dot { background: var(--warn); }
  .step-info  { border-left-color: var(--accent-2);} .step-info  .dot { background: var(--accent-2); }

JS — add renderRunTimeline(run) returning an HTML string of <div class="timeline">...steps...</div>.
Build a step only when its data is present, in this order; helper step(cls,title,detail).
  1. step-info  "Input received"      -> run.prompt (truncate long)
  2. step-info  "Prompt structured"   -> ONLY if run.optimized; detail = preserved count / optimized note
  3. (compression) if run.compressed: step-info "Context compressed" detail = compressionLabel(run);
     else step "Context kept" (class step-muted via plain .timeline-step) detail = run.route_note
  4. step-info  "Model answered"       -> detail = `${run.decision.model || "model"} · ${run.decision.latency_ms} ms`
  5. "Output checked" -> class from run.decision.verdict: NOT_RULED_OUT->step-pass,
     RULED_OUT_WRONG->step-block, UNCHECKABLE->step-warn; detail = `${decision.validator}: ${decision.reason}`
  6. "Repair" -> ONLY if run.repair_attempts.length; class step-warn (or step-pass if final repaired ok);
     detail = `${run.repair_attempts.length} attempt(s)` + (run.exact_correction != null ? `, corrected: ${run.exact_correction}` : "")
  7. "Final decision" -> class from run.decision.final_status (accepted->step-pass, repaired->step-warn,
     rejected/escalated->step-block); detail = run.final_output (mark if != run.model_output)
  8. step-info  "Audit saved"         -> detail = run.audit_id + " " + replayButton(run.audit_id)
Use a case-insensitive verdict compare (String(v).toUpperCase()).

WIRE IT IN: in renderRunDetail(run), render in this order: the scorecard (renderScorecard(run.scorecard)),
then the timeline (renderRunTimeline(run)), then keep the EXISTING key/value grid + repair table inside a
collapsed <details><summary>raw fields</summary> ... </details> (move the current grid there; do not delete it).
Replay must still work (the thread delegates handleReplayClick).

TESTS (tests/test_web.py): in the served-page test assert response.text contains "renderRunTimeline"
and ".timeline-step". (No new run is required; these are static source assertions.)

DONE WHEN: gates pass; a /run shows a colour-coded received->compressed->model->checked->repaired->final->audit
lifecycle with the raw fields tucked under a collapsed section.
~~~

---

## Slice P2 — Plain-language verdict labels  [app.html only]

Goal: humans read "Blocked: provably invalid", machines still get `RULED_OUT_WRONG` in the audit JSON.

~~~text
SLICE P2 — plain-language verdicts. Shared context applies. Edit ONLY src/routemap_harness/web/app.html.

JS — add a display helper (place near verdictClass):
  function verdictLabel(value) {
    const key = String(value || "").toUpperCase();
    if (key === "RULED_OUT_WRONG") return "Blocked: provably invalid";
    if (key === "NOT_RULED_OUT")   return "No hard failure found";
    if (key === "UNCHECKABLE")     return "Needs escalation";
    return String(value || "");
  }

APPLY verdictLabel(...) for DISPLAY text everywhere a verdict token is shown to the user, keeping
verdictClass(...) for colour:
  - renderDecision: the "verdict" row value
  - renderAudit: the verdict cell
  - renderCompareResults: the verdict cell (keep the "unavailable" fallback)
  - renderAgent: tool_firewall / repair_firewall / output_check verdict text
  - renderRunTimeline (from P1): the "Output checked" + "Final decision" titles/details
Do NOT change: the raw-audit JSON <pre> in the replay modal, any value sent to the API, or audit records.

TESTS (tests/test_web.py): assert response.text contains "verdictLabel", "Blocked: provably invalid",
"No hard failure found", and "Needs escalation". (tests/test_api.py + tests/test_audit.py stay unchanged
and must still pass, since API/audit verdicts remain technical.)

DONE WHEN: gates pass; the UI reads in plain language while /audit and /check JSON still show RULED_OUT_WRONG etc.
~~~

---

## Slice P3 — Demo buttons  [app.html only]

Goal: one click loads a real example and runs it, so nobody has to invent a test case.

~~~text
SLICE P3 — demo buttons. Shared context applies. Edit ONLY src/routemap_harness/web/app.html.

HTML: directly under <div id="tab-help" ...></div> add:
  <div id="demo-bar" class="demo-bar">
    <span class="demo-label">Demos:</span>
    <button type="button" class="secondary" data-demo="unsafe-tool">Unsafe tool call</button>
    <button type="button" class="secondary" data-demo="broken-json">Broken JSON</button>
    <button type="button" class="secondary" data-demo="long-context">Long-context compression</button>
    <button type="button" class="secondary" data-demo="wrong-arith">Wrong arithmetic (needs model)</button>
  </div>

CSS:
  .demo-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0 0 16px; }
  .demo-bar .demo-label { color: var(--muted); font-size: 0.82rem; font-weight: 700; }
  .demo-bar button { width: auto; min-height: 32px; padding: 5px 10px; font-size: 0.82rem; }

JS: add a click handler on #demo-bar that dispatches on event.target.dataset.demo, then runs the matching
sample using the EXISTING fields/handlers and requestSubmit():
  - "unsafe-tool":  taskSelect.value="tool_call";
      outputField.value = '{"name":"delete_file","arguments":{"path":"../../system32/config"}}';
      allowedToolsField.value="read_file, delete_file"; specField.value="";
      syncTaskFields(); setMode("check"); checkForm.requestSubmit();
  - "broken-json":  taskSelect.value="json_schema";
      outputField.value = '{ "id": "x", "score": 104, "status": "maybe", "tags": [] }';
      specField.value = the default schema already in the page (id/score 0..100/status enum/tags minItems 1);
      allowedToolsField.value=""; syncTaskFields(); setMode("check"); checkForm.requestSubmit();
  - "long-context": labPassage.value = a ~60-word passage mixing filler ("the of and to ...") with one key
      sentence ("The verifier must not drop negated risk statements before release.");
      labQuestion.value="What must the verifier not drop?"; setMode("lab"); labForm.requestSubmit();
  - "wrong-arith":  promptField.value="What is 47 * 89? Reply with the number only.";
      setMode("run"); chatForm.requestSubmit();   // needs a model; if none, the existing error shows
Reuse existing localStorage writes that the submit handlers already do. No new endpoints.

TESTS (tests/test_web.py): assert response.text contains 'id="demo-bar"' and each of
'data-demo="unsafe-tool"', 'data-demo="broken-json"', 'data-demo="long-context"', 'data-demo="wrong-arith"'.

DONE WHEN: gates pass; each button jumps to the right tab, fills a sample, and shows RouteMap working
(the first three need no model).
~~~

---

## Slice P4 — Fix the /repair dead-end  [api.py + app.html + tests]

Goal: the Check-tab "repair" button currently calls a stub. Make /repair actually repair the current
payload with the selected model, returning the repaired decision + attempts. Keep the CLI stub intact.

~~~text
SLICE P4 — wire /repair. Shared context applies. Edit api.py + app.html + tests/test_api.py.

BACKEND (src/routemap_harness/api.py) — replace the BODY of the POST /repair handler (repair_decision):
  payload = _check_payload(body)
  model_ref = str(body.get("model_ref") or DEFAULT_MODEL_REF)
  runtime = str(body.get("runtime") or "ollama")
  payload["model_ref"] = model_ref
  payload["runtime"] = runtime
  payload["auth_mode"] = _auth_mode(runtime)
  base = harness_check(payload, strict=bool(body.get("strict")))
  base = _with_model_record(base, model_ref)
  audit_store.append(base, _audit_path())
  if base.verdict == "NOT_RULED_OUT":
      out = _api_decision(base); out["scorecard"] = scorecard(base.to_dict())
      out["attempts"] = []; out["repaired"] = False; out["note"] = "nothing to repair"
      return out
  try:
      result = repair(base, payload, model_fn, max_retries=2, audit_path=_audit_path())
  except (ModelAdapterUnavailable, ModelAdapterError) as exc:
      raise HTTPException(status_code=503, detail=f"repair needs a model (start Ollama or set an API key): {exc}")
  final = _with_model_record(result.final_decision, model_ref)
  out = _api_decision(final)
  out["scorecard"] = scorecard(final.to_dict())
  out["attempts"] = [a.to_dict() for a in result.attempts]
  out["repaired"] = final.final_status == "repaired"
  out["exact_correction"] = _exact_correction(payload, final)
  return out
Keep the repair_stub import and the offline CLI path in __main__.py UNCHANGED (the stub still serves the CLI).

FRONTEND (src/routemap_harness/web/app.html) — the repair button handler:
  - Send the CURRENT check form + selected model:
      body = { task: taskSelect.value || null, output: outputField.value, spec: parseSpec(),
               allowed_tools: parseAllowedTools(), source: sourceField.value || null,
               strict: strictField.checked,
               model_ref: modelSelect.value,
               runtime: (modelSelect.selectedOptions[0] && modelSelect.selectedOptions[0].dataset.runtime) || "ollama" }
  - POST /repair, then renderDecision(response) (it renders the scorecard too).
  - After rendering, set statusEl.textContent to a short summary: response.note || (response.repaired
      ? `repaired (${(response.attempts||[]).length} attempt(s))` : "could not repair — escalated") +
      (response.exact_correction != null ? `, corrected: ${response.exact_correction}` : "").
  - On a non-OK response show the error text in statusEl (the existing request() helper throws with the body).

TESTS (tests/test_api.py):
  - REPLACE test_api_repair_stub with test_api_repair_runs_model_and_repairs:
      monkeypatch.setattr(api, "model_fn", lambda prompt, **kw: '{"id":"x","score":88,"status":"pass","tags":["ok"]}')
      POST /repair {task:"json_schema", output:'{"id":"x","score":104,"status":"maybe","tags":[]}',
        spec: <the score 0..100 / status enum / tags minItems1 schema>, model_ref:"unit-test"}
      assert 200; body["repaired"] is True; body["attempts"] non-empty; body["decision"]["final_status"]=="repaired".
  - ADD test_api_repair_no_model_returns_503:
      def boom(prompt, **kw): raise api.ModelAdapterUnavailable("no model")
      monkeypatch.setattr(api, "model_fn", boom)
      POST /repair with the same wrong json_schema payload; assert response.status_code == 503.
  (api.ModelAdapterUnavailable is importable from the api module since it's imported there.)

DONE WHEN: pytest -q + run_evidence.py + git diff --check all pass; clicking "repair" on a ruled-out Check
actually repairs via the selected model (or shows a clean 503 message when no model is available); the
audit JSON and decision schema are unchanged.
~~~

---

## After the four slices
- `git diff --check && python -m pytest -q && python run_evidence.py`
- Optional next polish (not specced here): a Dashboard headline ("blocked N · repaired M · escalated K ·
  tokens saved X%"), a per-lane coverage checklist in the scorecard, and making `/compare` return model
  metadata from `_run_once` instead of the module-global `_LAST_MODEL_METADATA` (thread-safety).
