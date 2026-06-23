# Route Extraction Benchmark Design — Seed Document

## Source Metadata
- Primary URL: local://routemap-benchmark-design
- Benchmark note: original RouteMap-oriented route-note document, not a copied source page.

## Route Sections

### BACKGROUND
A RouteMap benchmark needs documents that contain definitions, methods, claims, examples, limitations, results, and next steps.

### DEFINE
A route label describes the job a passage performs in a document, such as defining a term, stating a claim, reporting a result, or identifying a limitation.

### METHOD
A human annotator should label each passage by role, entity, operative status, and relation before model evaluation.

### CLAIM
Route-based retrieval should be most useful when the answer depends on structural roles rather than simple keyword overlap.

### RESULT
Previous sandbox tests showed strong gains on synthetic and silver-label real-document retrieval, but human-gold validation is still required.

### LIMITATION
A benchmark built only from route-friendly documents may overestimate performance; future corpora should include ambiguous and adversarial passages.

### NEXT_STEP
The next benchmark version should include 100 to 300 human-labelled passages and 20 to 75 QA queries.

### EXAMPLE
A question asking for a compliance process may require a DEFINE passage, a METHOD passage, and a LIMITATION passage.