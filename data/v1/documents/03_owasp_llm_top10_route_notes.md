# OWASP Top 10 for LLM Applications — Route Notes

## Source Metadata
- Primary URL: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- Alternate URL: https://genai.owasp.org/llm-top-10/
- Benchmark note: original RouteMap-oriented route-note document, not a copied source page.

## Route Sections

### BACKGROUND
OWASP maintains a security project focused on common risks in large language model applications.

### DEFINE
An LLM application risk is a vulnerability pattern that can allow the model, surrounding tools, data pipeline, or agent workflow to behave insecurely or expose sensitive information.

### CLAIM
LLM security differs from ordinary web security because prompts, tool access, retrieval context, model outputs, and agent autonomy all become part of the attack surface.

### METHOD
A practical security review should identify prompt injection risks, insecure output handling, data exposure risks, tool or plugin risks, supply chain issues, and overreliance on generated content.

### EXAMPLE
Prompt injection should be annotated as a threat route where untrusted input modifies the model's intended instruction path.

### LIMITATION
A top-ten list is useful for prioritisation but it is not a complete threat model for every product, sector, or deployment context.

### NEXT_STEP
For RouteMap, this source is useful for testing whether the extractor identifies risk definitions, mitigation methods, and concrete examples.

### RESULT
This document should create labels across DEFINE, METHOD, CLAIM, LIMITATION, and EXAMPLE.