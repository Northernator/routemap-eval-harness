# Running RouteMap locally

Get the harness tested and the cockpit running. After cloning, run everything from the repository root:

```powershell
git clone https://github.com/Northernator/routemap-eval-harness.git
cd routemap-eval-harness
```

## 1. Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then re-run the activate line.
On bash/macOS, activate with `source .venv/bin/activate`.

## 2. Install
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt      # editable project + dev/API/benchmark tools
```
- `requirements-dev.txt` installs the project editable, so you get the `routemap-harness` CLI without
  setting `PYTHONPATH`.
- Core = numpy · dev/API = pytest / jsonschema / fastapi / uvicorn / httpx · benchmark = pandas / matplotlib.

> No-install alternative: skip `pip install -e .` and instead run `$env:PYTHONPATH = "src"` in every new terminal, then use `python -m routemap_harness ...` in place of `routemap-harness ...`.

## 3. Run the tests
```powershell
python -m pytest -q
python scripts/check_acceptance.py
```
All discovered tests and acceptance checks must pass; the exact test count can grow. Then run the curated
evidence suite and offline benchmarks:
```powershell
python run_evidence.py            # writes EVIDENCE\RESULTS.md
```

## 4. Start the cockpit
```powershell
routemap-harness serve                     # http://127.0.0.1:8000/
# dev auto-reload:  routemap-harness serve --reload
# different port:   routemap-harness serve --port 8001
```
Open http://127.0.0.1:8000/ in a browser.

## 5. Test each tab
**No model needed:**
- **Check** — leave task on `json_schema`; the prefilled output has `score: 104` vs a schema max of 100, so it returns `ruled_out_wrong` with an honest coverage scorecard. Try the `tool_call` and `grounded_qa` tasks too (paste a tool-call JSON / an answer + source).
- **Lab** — paste a paragraph and a question, hit route: green = kept, grey = cheap-routed, red = protected, yellow = question-overlap, plus the compressed prompt that would be sent.
- **Dashboard** — after you've run a few Checks/Runs, shows the failure genome (counts, per-model, false accepts, latency) and an "export failures (JSONL)" button.

**Needs a model (see step 6):**
- **Run** — pick the ollama model, enter a prompt (e.g. `2 + 3`), optionally toggle "compress long context" / "structure prompt"; see prompt sent, raw vs final output, repairs, tokens saved, latency. Wrong arithmetic gets an exact correction.
- **Compare** — tick 2+ models, one prompt, get a verdict/tokens/cost/time table.
- **Agent** — goal like `Use the calculate tool to add 2 and 3`: plan → firewalled tool call → output check → final, each step replayable.

## 6. Ollama (for Run / Compare / Agent)
```powershell
ollama serve            # if not already running (separate terminal)
ollama pull llama3.1    # one time
ollama list             # confirm it's there
```
The adapter calls `http://127.0.0.1:11434`. Optional cloud models — set before `serve` to light them up in Compare:
```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```
Use real credentials only in your local environment. Never paste keys into issues, screenshots, fixtures,
audit logs, or committed files. Cloud calls can transmit prompts to a provider and may incur charges.

## 7. CLI smoke tests (no UI)
```powershell
routemap-harness validate-config                                   # lane registry vs schema
routemap-harness route --passage data\v1\documents\01_nist_ai_rmf_route_notes.md --question "what reviews claims?"
routemap-harness summarize --audit data\outputs\audit.jsonl        # after some runs
```

## Troubleshooting
- **`No module named routemap_harness`** — you skipped `pip install -e .` and didn't set `$env:PYTHONPATH = "src"`, or you're not in the package root.
- **API/web tests show as skipped** — install `httpx` (step 2).
- **Run/Compare/Agent hangs or errors** — Ollama isn't running or the model isn't pulled (`ollama list`).
- **Port already in use** — `routemap-harness serve --port 8001`.
- **Activation blocked** — `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (step 1).

For contribution workflow, generated-output boundaries, and review gates, see [`../CONTRIBUTING.md`](../CONTRIBUTING.md).
