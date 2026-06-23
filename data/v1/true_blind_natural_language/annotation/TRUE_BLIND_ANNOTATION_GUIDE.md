# True-Blind Annotation Guide

This guide is for fresh natural-language RouteMap documents only. Do not copy old gold rows into this test. Use older guidelines only as label convention references.

## Human Checkpoint

Fill `true_blind_annotation_batch.csv` manually, then save the completed file as:

`data/v1/true_blind_natural_language/annotation/true_blind_gold.csv`

Predictions must not be run until this gold file exists and validates. Gold labels must not be used to tune prompts, taxonomies, mappings, thresholds, evaluator logic, combined_v3, D, or R6.

## Required Columns

- `doc_id`: stable raw document identifier; do not edit.
- `segment_id`: stable `TB001`, `TB002`, ... identifier; do not edit.
- `source_doc`: source filename; do not edit.
- `title`: source filename or document title; do not edit unless correcting a source typo.
- `segment_index`: zero-based source segment order; do not edit.
- `context_before`: previous segment text for context; do not label this field.
- `segment_text`: segment being labeled.
- `text`: same label target as `segment_text`; kept for existing prediction/evaluation scripts.
- `context_after`: next segment text for context; do not label this field.
- `gold_role`: human role label.
- `gold_entities`: semicolon-separated human entity labels.
- `gold_operative_status`: human operative-status label.
- `gold_relation`: human relation label.
- `gold_answer_relevant`: human answer relevance label.
- `notes`: optional annotation note.

## Role

Choose one fine role:

- `BACKGROUND`: context, motivation, history, framing.
- `CLAIM`: assertion, recommendation, principle, requirement-like statement.
- `DEFINE`: definition or scope statement.
- `METHOD`: procedure, workflow, test, measurement, or implementation instruction.
- `RESULT`: observed outcome, measured result, conclusion from applying a method.
- `LIMITATION`: caveat, weakness, exclusion, boundary, failure mode.
- `NEXT_STEP`: planned future work, proposed follow-up, open action.
- `EXAMPLE`: illustrative case or non-binding example.

## Entities

Write readable concepts, systems, actors, standards, artifacts, or objects mentioned in the segment.

Use semicolons:

```text
retrieval audit; policy exception; reviewer queue
```

Keep boundaries conservative. Prefer stable concepts over every noun phrase. Empty entities are allowed only if the segment truly has no meaningful route entities.

## Operative Status

Choose one:

- `ACTIVE`: statement applies, recommends, asserts, measures, or instructs.
- `CONDITIONAL`: statement depends on a condition, threshold, context, or "if/when".
- `LIMITED`: statement is partial, constrained, incomplete, scoped, or qualified.
- `NEGATED`: statement says something is absent, false, insufficient, or not allowed.
- `DESCRIPTIVE`: neutral background, definition, or context without strong action/constraint.

## Relation

Use the main relation expressed by the segment. Valid values are:

- `asserts`
- `defines`
- `gives_example`
- `limits`
- `maps_to`
- `proposes_next_test`
- `recommends`
- `reports_usefulness`
- `sets_context`
- `supports_retrieval`
- `warns_about`
- `requires`

If none fit, use the closest existing convention and explain in `notes`; do not invent labels for this benchmark without updating validation deliberately before annotation begins.

## Answer Relevance

Choose one:

- `YES`: likely useful evidence for route-based QA.
- `NO`: unlikely to answer directly.
- `MAYBE`: useful only for some query framings.

## Mini Examples

These examples are newly written for this guide, not copied from blind rows.

```text
Text: The review queue stores each rejected citation with the policy check that blocked it.
gold_role = METHOD
gold_entities = review queue; rejected citation; policy check
gold_operative_status = ACTIVE
gold_relation = supports_retrieval
gold_answer_relevant = YES
```

```text
Text: The earlier dashboard showed ticket counts, but it did not preserve the reason each ticket moved between teams.
gold_role = LIMITATION
gold_entities = dashboard; ticket counts; team transfer reason
gold_operative_status = NEGATED
gold_relation = limits
gold_answer_relevant = MAYBE
```
