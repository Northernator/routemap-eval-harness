# RouteMap — Lab Mode Roadmap

**From "AI output checker" to "AI reliability cockpit."**

Status: 2026-06-24 · Owner: Chris · Scope: product/UX surface over the existing harness (not new theory).
Companion build file: `PROMPT_SHEET_LAB_MODE.md` (paste-ready Codex specs, one slice at a time).

---

## 1. The reframe

The harness already routes, compresses, verifies, repairs, escalates, and logs. The UI only shows two of those lanes (Check and Chat), so the product *feels* like an arithmetic checker even though the architecture underneath is a full control layer for AI runs.

This roadmap does **not** add new math or theory. It closes the gap between what the harness already does and what a user can see and trust. Almost every item below is *surfacing or extending code that already exists*.

**North-star sentence:**

> RouteMap is an AI reliability cockpit: run any model, compress the input, verify the output, repair what can be repaired, escalate what cannot, and log every decision.

---

## 2. What already exists (grounded inventory)

This is the proof that it is *not* "only arithmetic." Every row is real code in `routemap_eval_harness/routemap_eval_harness/`.

| Capability | Where it lives | Status |
| --- | --- | --- |
| Element token router (33 functional ELEMENTS + codon motif scoring), promoted default | `src/routemap_token/elements.py`, `routers.py:route_passage` | DONE |
| Per-token routing rows (keep / cheap + score) | `src/routemap_harness/core.py:route_tokens` | DONE — element/query-overlap not yet surfaced for a UI |
| Input compression inside the run path | `src/routemap_harness/api.py:_optimize_prompt` → `route_passage`; returns `tokens_before/after/reduction/compressed/route_note` | DONE — invisible in UI |
| Harness decision (route → validate → verdict → action → final_status) | `core.py:harness_check`, `HarnessDecision` | DONE |
| Verifier-guided retry / repair + exact arithmetic correction | `src/routemap_harness/policy.py:repair`, `api.py:_exact_correction` | DONE |
| Model adapters: Ollama, OpenAI, Anthropic (+ CLI placeholders, disabled) with rich call metadata | `src/routemap_harness/adapters.py:model_fn`, `ModelCallMetadata` | DONE |
| Strict audit log (JSONL) + full summary metrics | `src/routemap_harness/audit_store.py:summarize_records` | DONE — **this is the entire Failure Genome dataset**, no UI yet |
| Lanes: arithmetic, json_schema, python_code, long_context_qa, retrieval | `src/routemap_controller/controller.py:route_decide` | DONE |
| HTTP surface: `/`, `/models`, `/check`, `/run`, `/repair`, `/audit`, `/audit/{id}` | `src/routemap_harness/api.py` | DONE |
| Control page UI — **Check and Chat tabs only** | `src/routemap_harness/web/app.html` (single file, vanilla JS) | PARTIAL — this is the gap |

The takeaway: the backend for the visualizer, the model comparison, the failure dashboard, and the audit replay is *already written*. The work is mostly the front of the cockpit plus two new validation lanes.

---

## 3. Phases

Ordered **Lab Mode first** (make the existing harness feel alive), then the two commercially-valuable lanes, then trust/diagnostics, then active prep and export. Each sub-item maps to one slice in `PROMPT_SHEET_LAB_MODE.md`.

### Phase 1 — Lab Mode (surface what exists) — *lead*

The single most important upgrade: make the token optimizer and the multi-model run visible.

- **1A — Before/After token visualizer.** A new `POST /route` endpoint returns per-token rows (token, route_action, element, query_overlap, protected). The UI renders the original text token-by-token: green = kept, grey = cheap-routed, red = protected/cannot-drop (NEGATION, CODE, CITATION, INSTRUCT, RISK), yellow = question overlap, then the compressed prompt actually sent. Turns the invisible optimizer into the headline feature. Built from existing routing code.
- **1B — Run cockpit tab.** Promote Chat into a proper Run tab that shows, per run: prompt → prompt_sent (with compression chip), raw output, final output, verdict/action/final_status, repair attempts, tokens before/after, latency. `/run` already returns all of this.
- **1C — Compare (multi-model).** A new `POST /compare` runs one prompt across several selected models and returns a row per model: output, verdict, repair, tokens, cost, latency. Reuses `model_fn` + `harness_check` per model. This is the "AI lab" demo.

### Phase 2 — Flagship lanes

- **2A — Tool-call firewall.** New `tool_call` task type + lane: validate a proposed tool call's JSON against a schema, check required fields, reject unsafe paths / invalid dates / impossible numbers / disallowed tool names, repair if safe, only then mark executable. Sits in front of any agent tool call. Likely the most commercially valuable feature in the list.
- **2B — Citation / source grounding.** New `grounded_qa` lane for RAG/document workflows. Start simple (no full NLI): every named entity in the answer appears in the source, claimed numbers/dates exist in the source, a source id is cited, the evidence span contains answer terms. Unsupported claim → escalate. Makes RouteMap useful for legal/research/compliance.

### Phase 3 — Diagnostics & trust

- **3A — Failure Genome dashboard.** A `/summary` endpoint over `audit_store.summarize_records` (extended with a by-model breakdown) plus a dashboard tab: failures by type, escalations, repairs successful, false accepts, latency. The data already exists; this is a reporting layer.
- **3B — Replay mode.** "Replay this decision" reconstructs a run: original input, model, prompt sent, compression applied, raw output, validators run, repair prompt, final output, audit record. Requires a new **run store** (see guardrails) because the decision schema is intentionally locked.

### Phase 4 — Active prep & export

- **4A — Prompt optimizer (structured prep).** Use the element tagger to rewrite a loose prompt into a structured task spec (task, preserve numbers/negations/entities/citations, return-format) before the model sees it. Gives the harness an active "prep" role, not just a checking role.
- **4B — RouteMap coverage scorecard (honest, not fake confidence).** A scorecard, never a truth score: validation coverage %, hard failures, unchecked claims, repair attempts, escalation required, input compression %, source grounding partial/full. Language is "72% of this output was covered by checkable routes," never "95% correct."
- **4C — Failures → training JSONL export.** "Export failures as training data" emits JSONL (`prompt`, `model_output`, `failure_type`, `validator_reason`, `repair_prompt`, `corrected_output`, `final_status`) from the run store + audit. Makes RouteMap useful for later fine-tuning.

### Phase 5 — Agent control loop (minimal) — *stretch*

A small, bounded loop: plan → check plan → run tool → check tool input (reuses 2A) → check tool output → repair/escalate → final. Ship the minimal version only; full autonomous orchestration stays in the parking lot.

---

## 4. Parking lot (explicitly deferred)

Not next. Each is parked on purpose so the build stays on the "make it feel alive" line:

- **Custom model fine-tuning** — 4C produces the data; training is a separate later track.
- **RNS compute** — already flagged "do later"; no product surface depends on it.
- **Matrix / KV-attention** — `routemap_matrix` exists for research; not on the product path.
- **Heavy dashboard polish** — ship functional dashboards first.
- **Many provider integrations** — three real adapters is enough to prove Compare; add more on demand.
- **Full autonomous agent orchestration** — only the minimal loop in Phase 5.

---

## 5. Design guardrails (so growth doesn't break what's validated)

These are load-bearing — they keep the validated core intact as the surface grows:

1. **No-leak routing stays no-leak.** Routing and the visualizer never read a gold answer or evidence label. The visualizer shows only inference-time signals (element, query overlap, score).
2. **The decision schema is frozen.** `schemas/harness_decision_v1.schema.json` is `additionalProperties:false`. Run-level I/O for Replay and Export (prompt, prompt_sent, model_output, repair_prompt, final_output, model metadata) goes in a **new run store** (`data/outputs/runs.jsonl`) keyed by `decision_id` — never shoved into the decision record.
3. **Determinism preserved.** Temperature 0, fixed seeds, deterministic adapters — same as today.
4. **Honest scoring only.** Coverage and checkable-route language, never a fabricated correctness probability.
5. **Every new lane ships with tests + evidence.** A `pytest` file under `tests/` (or a root `r*_test_*.py`) and a new entry in `run_evidence.py:STEPS`, so `python run_evidence.py` keeps covering the whole system.

---

## 6. Sequencing map

| Slice | Phase | Primarily touches | Depends on | Demo when done |
| --- | --- | --- | --- | --- |
| 1 — `/route` + token visualizer | 1A | `core.py`, `routers.py`, `api.py`, `app.html` | — | Paste text, see green/grey/red/yellow tokens + compressed prompt |
| 2 — Run cockpit tab | 1B | `app.html` | 1 (shares route view) | Run a prompt, see full pipeline in one panel |
| 3 — `/compare` + Compare tab | 1C | `api.py`, `app.html` | 2 | One prompt, table across Ollama/OpenAI/Anthropic |
| 4 — Tool-call firewall lane | 2A | `classify.py`, `controller.py`, `routemap_validators/`, `core.py`, `app.html` | — | Invalid/unsafe tool call rejected + repaired |
| 5 — Citation grounding lane | 2B | `classify.py`, `controller.py`, `routemap_validators/`, `core.py`, `app.html` | — | Unsupported claim escalated; grounded claim passes |
| 6 — Failure Genome dashboard | 3A | `audit_store.py`, `api.py`, `app.html` | 4, 5 (richer data) | Dashboard of failures by type and model |
| 7 — Run store + Replay | 3B | new `run_store.py`, `api.py`, `app.html` | 2 | Click a decision, replay the whole run |
| 8 — Prompt optimizer | 4A | new `routemap_prompt/` or `routemap_token`, `api.py`, `app.html` | 2 | Loose prompt → structured spec toggle |
| 9 — Coverage scorecard | 4B | `core.py`/validators, `api.py`, `app.html` | 4, 5 | Honest coverage card on each result |
| 10 — Failures → JSONL export | 4C | `run_store.py`, `api.py`, `app.html` | 7 | Download training JSONL of failures |
| 11 — Minimal agent loop | 5 | new `routemap_agent/`, `api.py`, `app.html` | 4 | plan → tool-check → output-check → final |

---

## 7. Definition of done (every slice)

A slice is done only when all of these pass, run from `routemap_eval_harness/routemap_eval_harness/`:

- `pytest -q` green (existing + the slice's new tests).
- `python run_evidence.py` completes clean, including the slice's new `STEPS` entry.
- `git diff --check` clean (no whitespace errors).
- No new runtime dependency beyond `requirements-api.txt` (fastapi, uvicorn, pydantic) unless the slice says so.
- The demo in the sequencing table works against a live server (`PYTHONPATH=src uvicorn routemap_harness.api:app`).
- No-leak and the frozen decision schema are both still intact.
