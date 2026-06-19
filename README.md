# RouteMap Evaluation Harness

This project is a practical evaluation harness for testing RouteMap properly against the remaining hard requirements:

1. Human-gold labels
2. Modern neural embedding baseline
3. LLM-based route extraction
4. Real QA judged by humans or an evaluator model
5. Larger document collections

It is designed so you can start small with CSV files and later plug in real APIs or local models.

---

## What RouteMap is testing

RouteMap treats a document as more than text chunks. Each passage is mapped into structured route fields:

```text
document_scope + entity + role + relation + operative_status
```

Then retrieval can be sparse:

```text
query -> route extraction -> small candidate set -> answer generation
```

The key claim to test:

> Can a typed semantic route index reduce comparisons while preserving or improving retrieval and answer quality?

---

## Main scripts

```text
src/run_local_demo.py
src/run_batch_eval.py
src/generate_run_report.py
src/build_annotation_batch.py
src/build_gold_sample.py
src/validate_gold_labels.py
src/run_baselines.py
src/run_routemap.py
src/run_neural_embeddings.py
src/run_llm_route_extractor.py
src/score_route_extraction.py
src/generate_answers.py
src/judge_answers.py
src/run_qa_eval.py
src/score_results.py
```

---

## Local setup

Use Python 3.10+.

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux, activate with:

```bash
source .venv/bin/activate
```

The required demo dependencies are only `pandas` and `numpy`.

Optional neural embedding baseline dependency:

```bash
python -m pip install sentence-transformers
```

---

## Data files

Put real `.txt` or `.md` documents in:

```text
data/documents/
```

Human annotation templates live in:

```text
data/gold/
```

Outputs are written to:

```text
data/outputs/
```

---

## One-command local demo

Run the full offline demo:

```bash
python src/run_local_demo.py
```

Or, if `make` is installed:

```bash
make demo
```

This command:

1. builds a gold-sample segment CSV from `data/documents/`
2. runs the keyword baseline on the filled sample gold files
3. runs the RouteMap gold-route baseline
4. runs the LLM route-extractor offline stub without any API call
5. scores CSV outputs under `data/outputs/`

Expected demo inputs:

```text
data/gold/gold_segments_filled.csv
data/gold/gold_qa_filled.csv
```

Expected demo outputs:

```text
data/outputs/gold_segments_sample.csv
data/outputs/baseline_results.csv
data/outputs/routemap_results.csv
data/outputs/llm_route_labels_offline_stub.csv
```

No external API is required for the demo path.

The offline demo does not import or require `sentence-transformers`.

---

## Batch corpus evaluation

Run the full workflow into a timestamped results folder:

```bash
python src/run_batch_eval.py --documents data/documents --gold-segments data/gold/annotation_batch_filled.csv --gold-qa data/gold/gold_qa_filled.csv --out data/runs
```

Run directory format:

```text
data/runs/YYYYMMDD_HHMMSS/
```

The batch runner executes, in order:

1. keyword baseline
2. RouteMap baseline
3. neural embedding baseline when `sentence-transformers` is installed and neural is not disabled
4. LLM route extraction, defaulting to offline `stub`
5. route extraction scoring
6. answer generation for keyword, RouteMap, and neural when available
7. QA judging
8. retrieval score summary

Disable optional neural work:

```bash
python src/run_batch_eval.py --documents data/documents --gold-segments data/gold/annotation_batch_filled.csv --gold-qa data/gold/gold_qa_filled.csv --out data/runs --disable-neural
```

Batch outputs include:

```text
baseline_results.csv
routemap_results.csv
neural_embedding_results.csv
llm_route_labels.csv
route_extraction_scores.csv
answers_keyword.csv
answers_routemap.csv
answers_neural.csv
qa_judgement_scores.csv
qa_judgement_summary.csv
run_summary.md
run_manifest.json
report.md
report.html
charts/
```

`neural_embedding_results.csv` and `answers_neural.csv` are present only when the optional neural baseline runs.

`run_manifest.json` records timestamp, git commit, corpus counts, QA count, methods run, Python version, and optional dependency detection.

`run_summary.md` includes retrieval comparison, route extraction summary, QA judgement summary, comparison reduction summary, and known limitations.

Generate or refresh the shareable report for an existing run:

```bash
python src/generate_run_report.py --run-dir data/runs/<timestamp>
```

Report outputs:

```text
report.md
report.html
charts/retrieval_comparison.png
charts/qa_judgement.png
charts/comparison_reduction.png
charts/route_extraction_scores.png
```

---

## Route roles

Default roles:

```text
DEFINE
CLAIM
METHOD
RESULT
LIMITATION
NEXT_STEP
EXAMPLE
BACKGROUND
```

For contract/code/dependency tasks, add:

```text
MODIFY
EXCEPT
SUPPORTS
CONTRADICTS
DEPENDS_ON
```

---

## Human annotation workflow

Create an annotation batch from documents:

```bash
python src/build_annotation_batch.py --docs data/documents --out data/gold/annotation_batch.csv
```

Annotators fill:

```text
gold_role
gold_entities
gold_operative_status
gold_relation
gold_answer_relevant
notes
```

Use the field vocabulary in:

```text
data/gold/ANNOTATION_GUIDELINES.md
configs/route_schema.json
```

Save the completed file as:

```text
data/gold/annotation_batch_filled.csv
```

Validate completed labels:

```bash
python src/validate_gold_labels.py --gold data/gold/annotation_batch_filled.csv
```

Validation checks:

- required columns exist
- required labels are not empty
- `gold_role` values match `configs/route_schema.json`
- `gold_operative_status` values match `configs/route_schema.json`
- `gold_relation` values match `configs/route_schema.json`
- `gold_answer_relevant` uses `0`, `1`, `yes`, `no`, `true`, or `false`

The repository includes a small filled sample at:

```text
data/gold/annotation_batch_filled.csv
```

---

## Recommended evaluation flow

### Step 1 — Build a human-gold sample

```bash
python src/build_gold_sample.py --docs data/documents --out data/gold/gold_segments_template.csv
```

A human annotator fills:

```text
gold_role
gold_entities
gold_operative_status
gold_relation
gold_answer_relevant
```

### Step 2 — Run baselines

```bash
python src/run_baselines.py --gold-segments data/gold/gold_segments_filled.csv --gold-qa data/gold/gold_qa_filled.csv
```

This runs:

- keyword retrieval

Neural embedding retrieval is an optional separate integration. See "Optional integrations" below.

### Step 3 — Run RouteMap

```bash
python src/run_routemap.py --gold-segments data/gold/gold_segments_filled.csv --gold-qa data/gold/gold_qa_filled.csv
```

This runs deterministic RouteMap extraction and retrieval.

### Step 4 — Run QA evaluation

```bash
python src/run_qa_eval.py --gold data/gold/gold_qa_filled.csv
```

This scores whether answers used correct segments and whether answer quality passes human/evaluator criteria.

### Step 5 — Score everything

```bash
python src/score_results.py --outputs data/outputs
```

When `baseline_results.csv`, `routemap_results.csv`, and `neural_embedding_results.csv` are present, this prints one combined table:

```text
keyword vs RouteMap vs neural embeddings
```

---

## Optional integrations

### Neural embedding baseline

This is not part of the no-API demo because it needs the optional `sentence-transformers` package and may download a model the first time it runs.

```bash
python -m pip install sentence-transformers
python src/run_neural_embeddings.py --gold-segments data/gold/gold_segments_filled.csv --gold-qa data/gold/gold_qa_filled.csv
python src/score_results.py --outputs data/outputs
```

Default model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Output:

```text
data/outputs/neural_embedding_results.csv
```

Neural embeddings do not require API keys.

### Combined retrieval comparison

Run all retrieval methods, including the optional neural embedding baseline:

```bash
python src/run_baselines.py --gold-segments data/gold/gold_segments_filled.csv --gold-qa data/gold/gold_qa_filled.csv
python src/run_routemap.py --gold-segments data/gold/gold_segments_filled.csv --gold-qa data/gold/gold_qa_filled.csv
python src/run_neural_embeddings.py --gold-segments data/gold/gold_segments_filled.csv --gold-qa data/gold/gold_qa_filled.csv
python src/score_results.py --outputs data/outputs
```

The comparison table reports:

```text
Hit@K
MRR
comparisons/query
comparison reduction %
```

### LLM route extraction

The local demo runs `src/run_llm_route_extractor.py` in offline stub mode. Stub mode is deterministic and requires no API key.

```bash
python src/run_llm_route_extractor.py --segments data/gold/annotation_batch_filled.csv --out data/outputs/llm_route_labels.csv --provider stub
```

The runner accepts:

```text
--provider stub|openai|anthropic|ollama
--model optional-model-name
```

Stub mode copies existing gold labels when present. If labels are missing, it falls back to:

```text
role = BACKGROUND
operative_status = UNKNOWN
relation = background_to
entities = []
```

Provider outputs are parsed as strict JSON and validated against:

```text
configs/route_schema.json
```

Invalid provider outputs are written to:

```text
data/outputs/llm_route_errors.csv
```

The prompt template lives at:

```text
prompts/llm_route_extractor_prompt.md
```

To add a real provider call later, implement the selected branch in `call_provider()` inside `src/run_llm_route_extractor.py`:

```text
openai = call OpenAI Responses/Chat API and return JSON text
anthropic = call Anthropic Messages API and return JSON text
ollama = call local Ollama HTTP API and return JSON text
```

Keep API keys in environment variables or local secret stores, not in repository files.

Examples:

```bash
python src/run_llm_route_extractor.py --segments data/gold/annotation_batch_filled.csv --provider openai --model gpt-4.1-mini
python src/run_llm_route_extractor.py --segments data/gold/annotation_batch_filled.csv --provider anthropic --model claude-3-5-haiku-latest
python src/run_llm_route_extractor.py --segments data/gold/annotation_batch_filled.csv --provider ollama --model llama3.1
```

### Route extraction scoring

Compare LLM or stub route labels against human-gold annotation labels:

```bash
python src/score_route_extraction.py --gold data/gold/annotation_batch_filled.csv --pred data/outputs/llm_route_labels.csv --out data/outputs/route_extraction_scores.csv
```

Outputs:

```text
data/outputs/route_extraction_scores.csv
data/outputs/role_confusion_matrix.csv
data/outputs/status_confusion_matrix.csv
data/outputs/relation_confusion_matrix.csv
```

Metrics:

```text
role accuracy
operative_status accuracy
relation accuracy
entity exact match
entity partial overlap / Jaccard
invalid output count
```

### QA source evaluation

Generate extractive answers from retrieved passages:

```bash
python src/generate_answers.py --gold-qa data/gold/gold_qa_filled.csv --gold-segments data/gold/gold_segments_filled.csv --method routemap --out data/outputs/answers_routemap.csv
```

Supported methods:

```text
keyword
routemap
neural
```

`neural` uses the optional `sentence-transformers` dependency. `keyword` and `routemap` are offline and deterministic.

Answer CSVs include:

```text
query_id
query
method
answer
used_segment_ids
```

Judge generated answers against human-gold QA labels and required source segments:

```bash
python src/judge_answers.py --answers data/outputs/answers_routemap.csv --gold-qa data/gold/gold_qa_filled.csv --out data/outputs/qa_judgement_scores.csv
```

Outputs:

```text
data/outputs/qa_judgement_scores.csv
data/outputs/qa_judgement_summary.csv
```

Offline deterministic judge metrics:

```text
source_hit
all_required_sources_used
answer_contains_gold_terms
hallucination_flag_simple
correctness_proxy
completeness_proxy
```

The optional evaluator-model prompt lives at:

```text
prompts/qa_judge_prompt.md
```

Default judging does not call any model or require API keys.

If you already have generated answers with `query_id`, `answer`, and `used_segment_ids`, you can still run the older source-only evaluator:

```bash
python src/run_qa_eval.py --answers data/outputs/answers.csv --gold-qa data/gold/gold_qa_filled.csv
```

---

## Metrics

Retrieval:

```text
Hit@K
MRR
Precision@K
Recall@K
Comparisons per query
Comparison reduction %
```

Route extraction:

```text
role accuracy
entity accuracy
operative-status accuracy
relation accuracy
confusion matrix
```

QA:

```text
source hit
answer correctness
answer completeness
hallucination rate
citation correctness
```

Compression:

```text
raw bytes
verbose route bytes
compact route-ID bytes
compression %
```

---

## What counts as a strong result

A credible RouteMap result should show:

```text
similar or better Hit@K than keyword/embedding
better MRR
fewer comparisons
lower hallucination/source-miss rate
clear failure taxonomy
```

---

## Important limitation

This harness does not magically prove RouteMap. It creates the structure needed to test it properly.

The strongest future version uses:

- human labels
- modern embeddings
- LLM route extraction
- evaluator-model QA judging
- larger real document collections
