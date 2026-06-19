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
src/build_gold_sample.py
src/run_baselines.py
src/run_routemap.py
src/run_neural_embeddings.py
src/run_llm_route_extractor.py
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

The local demo runs `src/run_llm_route_extractor.py` in offline stub mode. To use a real LLM, edit `call_llm()` in that script and keep provider credentials outside the repository.

```bash
python src/run_llm_route_extractor.py --segments data/gold/gold_segments_filled.csv
```

### QA source evaluation

If you have generated answers with `query_id`, `answer`, and `used_segment_ids`, run:

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
