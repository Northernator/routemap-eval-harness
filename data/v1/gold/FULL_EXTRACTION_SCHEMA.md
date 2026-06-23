# Full Extraction Schema

This schema defines the first full RouteMap extraction labels for the v1 seed annotation set.

## gold_role

Allowed values:

- `BACKGROUND`
- `CLAIM`
- `DEFINE`
- `METHOD`
- `RESULT`
- `LIMITATION`
- `NEXT_STEP`
- `EXAMPLE`

Meaning: the main route role the segment performs.

## gold_entities

A semicolon-separated list of important entities, concepts, standards, actors, systems, or objects mentioned in the segment.

Examples:

- `NIST AI RMF; AI risk management; governance; measurement`
- `OWASP LLM Top 10; prompt injection; tool risk`
- `EU AI Act; high-risk AI; risk management system`

Keep entities readable and conservative. Prefer stable concepts over every noun phrase.

## gold_operative_status

Allowed values:

- `ACTIVE`
- `CONDITIONAL`
- `LIMITED`
- `NEGATED`
- `DESCRIPTIVE`

Meanings:

- `ACTIVE` = the passage says something should happen, exists, applies, or is recommended.
- `CONDITIONAL` = the passage depends on a condition, context, threshold, or "if/when".
- `LIMITED` = the passage describes a partial, incomplete, constrained, or scoped action.
- `NEGATED` = the passage says something does not happen, cannot happen, is insufficient, or is not true.
- `DESCRIPTIVE` = the passage gives background, definition, context, or neutral description without a strong action/constraint.

## gold_relation

A short controlled phrase describing the main relation in the segment.

Examples:

- `defines`
- `recommends`
- `warns_about`
- `limits`
- `requires`
- `maps_to`
- `supports_retrieval`
- `gives_example`
- `reports_usefulness`
- `sets_context`
- `proposes_next_test`

## gold_answer_relevant

Allowed values:

- `YES`
- `NO`
- `MAYBE`

Meanings:

- `YES` = likely useful evidence for answering a route-based QA question.
- `NO` = metadata/title/background unlikely to answer directly.
- `MAYBE` = contextually useful depending on the query.
