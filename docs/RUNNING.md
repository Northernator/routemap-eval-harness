# Running RouteMap locally (Windows / PowerShell)

Get the harness tested and the cockpit running. Run everything from the package root:

```powershell
cd C:\dev\RouteMap\routemap_eval_harness\routemap_eval_harness
```

## 1. Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then re-run the activate line.

## 2. Install
```powershell
pip install -e .                                   # installs all 7 packages + the routemap-harness command
pip install -r requirements-dev.txt -r requirements-api.txt httpx
```
- `-e .` (editable install) means you never have to set `PYTHONPATH` and you get the `routemap-harness` CLI.
- dev = numpy / pytest / jsonschema / pandas / matplotlib · api = fastapi / uvicorn / pydantic · httpx = FastAPI test client.

> No-install alternative: skip `pip install -e .` and instead run `$env:PYTHONPATH = "src"` in every new terminal, then use `python -m routemap_harness ...` in place of `routemap-harness ...`.

## 3. Run the tests (confirms all 11 slices + serve)
```powershell
python -m pytest -q
```
Expect ~62 passing. Then the curated evidence suite + offline benchmarks:
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
