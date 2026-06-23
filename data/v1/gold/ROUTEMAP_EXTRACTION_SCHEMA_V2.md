# RouteMap Extraction Schema V2

## Role Schema

Allowed fine roles:

- `BACKGROUND`: source, project, document, policy, benchmark, or contextual framing.
- `CLAIM`: reusable thesis or assertion about a system, risk, method, or principle.
- `DEFINE`: term, category, boundary, identity, or naming definition.
- `METHOD`: reusable procedure, workflow step, or action to perform.
- `RESULT`: observed, evaluated, measured, benchmarked, or reported outcome.
- `LIMITATION`: caveat, insufficiency, constraint, warning, boundary, or failure mode.
- `NEXT_STEP`: proposed future work, future benchmark, or follow-up test.
- `EXAMPLE`: concrete scenario, instance, user case, model case, or illustrative row.

## Coarse Taxonomies

`coarse_5`:

- `CONTEXT`: BACKGROUND
- `ASSERTION`: CLAIM, DEFINE, RESULT
- `ACTION`: METHOD, NEXT_STEP
- `CAVEAT`: LIMITATION
- `INSTANCE`: EXAMPLE

`coarse_4`:

- `CONTEXT`: BACKGROUND
- `CONTENT`: CLAIM, DEFINE, RESULT
- `ACTION`: METHOD, NEXT_STEP, EXAMPLE
- `CAVEAT`: LIMITATION

`coarse_3`:

- `CONTEXT`: BACKGROUND
- `SUBSTANTIVE`: CLAIM, DEFINE, METHOD, RESULT, NEXT_STEP, EXAMPLE
- `CAVEAT`: LIMITATION

## Entity Schema

Entities are semicolon-separated canonical names. Entity extraction should be ontology-backed and conservative. Examples include:

- `AI safety evaluation`
- `AI risk management`
- `answer support`
- `agent memory`
- `audit trail`
- `benchmark`
- `consent boundary`
- `controls`
- `data protection`
- `evidence selection`
- `evaluation`
- `gold labels`
- `governance`
- `human review`
- `incident response`
- `LLM application security`
- `mismatch review`
- `model release governance`
- `permission boundary`
- `policy context`
- `privacy`
- `retrieval`
- `retrieval trace`
- `risk management`
- `route extraction`
- `route provenance`
- `RouteMap`
- `RouteMap segment`
- `secure AI development`
- `source context`
- `tool-use security`

## Operative Status

Allowed values:

- `ACTIVE`
- `CONDITIONAL`
- `LIMITED`
- `NEGATED`
- `DESCRIPTIVE`

## Relation

Allowed values:

- `sets_context`
- `defines`
- `asserts`
- `recommends`
- `reports_usefulness`
- `limits`
- `warns_about`
- `gives_example`
- `proposes_next_test`
- `maps_to`
- `requires`
- `supports_retrieval`

## Answer Relevance

Allowed values:

- `YES`
- `NO`
- `MAYBE`
