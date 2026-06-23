# Long-Context Agent Memory — Seed Document

## Source Metadata
- Primary URL: local://long-context-agent-memory
- Benchmark note: original RouteMap-oriented route-note document, not a copied source page.

## Route Sections

### BACKGROUND
Long-context systems can fail when relevant information is present but not structurally connected to the question.

### DEFINE
Agent memory routing is the process of storing and retrieving information according to task role, entity, dependency, and state transition.

### CLAIM
A memory system should not treat every stored passage as equally relevant; it should prioritise passages that occupy the right route in the task.

### METHOD
A route-aware memory system can store compact identifiers for document scope, entity, role, relation, and source pointer.

### RESULT
A compact route index can reduce storage and comparison costs while preserving links to the raw source text.

### LIMITATION
Route compression can lose detail if the role or entity extraction is wrong, so fallback retrieval and source inspection are still needed.

### NEXT_STEP
A practical implementation should combine route retrieval with neural embeddings and keyword fallback.

### EXAMPLE
A coding agent may need the route from request handler to permission check to database write, not just files containing the word permission.