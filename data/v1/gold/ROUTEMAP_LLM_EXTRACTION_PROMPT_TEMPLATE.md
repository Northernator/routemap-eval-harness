# RouteMap LLM Extraction Prompt Template

You are extracting RouteMap annotations from one passage. Output only JSON matching this contract:

```json
{
  "role": "BACKGROUND",
  "entities": ["RouteMap"],
  "operative_status": "DESCRIPTIVE",
  "relation": "sets_context",
  "answer_relevant": "MAYBE",
  "rationale": "short explanation"
}
```

Do not infer beyond the passage. Use only the title and passage text. Return concise rationale.

## Roles

- `BACKGROUND`: source, document, project, benchmark package, README, policy, or context description.
- `CLAIM`: reusable thesis or assertion that could support an answer.
- `DEFINE`: meaning, identity, boundary, or naming function of a term.
- `METHOD`: reusable procedure, workflow, or action to perform.
- `RESULT`: observed, measured, evaluated, benchmarked, or reported outcome.
- `LIMITATION`: caveat, insufficiency, constraint, warning, or failure mode.
- `NEXT_STEP`: future work, future benchmark, or follow-up test.
- `EXAMPLE`: concrete scenario, instance, user case, model case, or illustrative row.

## Entities

Return canonical ontology entities as strings. Use semantically grounded labels such as `AI safety evaluation`, `model release governance`, `privacy`, `consent boundary`, `permission boundary`, `retrieval trace`, `route provenance`, `RouteMap`, `route extraction`, `benchmark`, `evaluation`, `human review`, `evidence selection`, `tool-use security`, `incident response`, `agent memory`, `audit trail`, `answer support`, `policy context`, `controls`, `risk management`, `source context`, `mismatch review`, `gold labels`, `RouteMap segment`, `secure AI development`, and `LLM application security`.

Do not emit generic `data` or `risk` when a more specific entity is available. Do not emit entities unsupported by the passage.

## Status, Relation, Relevance

- Use `DESCRIPTIVE` for BACKGROUND, DEFINE, RESULT, and EXAMPLE unless the passage clearly says otherwise.
- Use `ACTIVE` for CLAIM, METHOD, and NEXT_STEP unless strong negation applies.
- Use `LIMITED` or `NEGATED` for LIMITATION.
- Map relations by role: BACKGROUND=`sets_context`, DEFINE=`defines`, CLAIM=`asserts`, METHOD=`recommends`, RESULT=`reports_usefulness`, LIMITATION=`limits` or `warns_about`, NEXT_STEP=`proposes_next_test`, EXAMPLE=`gives_example`.
- Use `YES` if directly useful for answering. Use `NO` for pure metadata/source/package context. Prefer `MAYBE` for background answer relevance if query-dependent.

## Examples

Title: `release_packet.md`
Text: `A release packet records reviewer notes, audit trails, and unresolved caveats before model approval.`
Output:
```json
{"role":"BACKGROUND","entities":["model release governance","human review","audit trail"],"operative_status":"DESCRIPTIVE","relation":"sets_context","answer_relevant":"NO","rationale":"Document context for release governance artifacts."}
```

Title: `trace_eval.md`
Text: `The retrieval trace exposes which passages supported the final answer and which route segment failed.`
Output:
```json
{"role":"RESULT","entities":["retrieval trace","answer support","RouteMap segment"],"operative_status":"DESCRIPTIVE","relation":"reports_usefulness","answer_relevant":"YES","rationale":"Reports what the trace reveals."}
```
