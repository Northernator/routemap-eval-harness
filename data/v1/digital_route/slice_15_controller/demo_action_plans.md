# Unified Route Controller Demo

| Task | task_type | route_family | action | validator | outcome | compute_avoided |
| --- | --- | --- | --- | --- | --- | --- |
| wrong_arithmetic | arithmetic | digital_residue | verify | residue | RULED_OUT_WRONG | false |
| correct_arithmetic | arithmetic | digital_residue | verify | residue | NOT_RULED_OUT | false |
| bad_json | json_schema | sound_checker | verify | json_schema_constraints_v1 | RULED_OUT_WRONG | false |
| valid_code | python_code | sound_checker | verify | python_code_parse_v1 | NOT_RULED_OUT | false |
| passage_question | long_context_qa | token_importance | cheap_path | answer_span_recall_guard | accept | true |
| retrieval_query | retrieval | embedding_fingerprint | cheap_path | rerank_guard | accept | true |
| unknown_high_risk | unknown | full_compute | escalate | full_compute_validator | FULL_COMPUTE_WITH_VALIDATOR | false |

## Traces

### wrong_arithmetic

```text
classify: expression plus claimed_answer -> arithmetic
route: parse_expression('2 + 3') -> {'family': 'bigsum', 'values': [2, 3]}
validator: routemap_digital.verify with moduli=default
decision: action=verify outcome=RULED_OUT_WRONG; no cheap prune, guarded verification only
```

### correct_arithmetic

```text
classify: expression plus claimed_answer -> arithmetic
route: parse_expression('2 + 3') -> {'family': 'bigsum', 'values': [2, 3]}
validator: routemap_digital.verify with moduli=default
decision: action=verify outcome=NOT_RULED_OUT; no cheap prune, guarded verification only
```

### bad_json

```text
classify: task hint override -> json_schema
route: sound-checker validator package
validator: json_schema_constraints_v1
decision: action=verify outcome=RULED_OUT_WRONG; checker reason=$.score above maximum 100
```

### valid_code

```text
classify: task hint override -> python_code
route: sound-checker validator package
validator: python_code_parse_v1
decision: action=verify outcome=NOT_RULED_OUT; checker reason=no applicable checker ruled out this output
```

### passage_question

```text
classify: passage plus question -> long_context_qa
route: routemap_token prior/context/policy
validator: answer_span_recall_guard
decision: action=cheap_path kept=8 cheap=10 reduction=0.556
```

### retrieval_query

```text
classify: query plus retrieval corpus -> retrieval
route: routemap_embedding RandomProjectionLSH candidates
validator: rerank_guard full cosine reranks the shortlist
decision: action=cheap_path shortlist=['b', 'c']
```

### unknown_high_risk

```text
classify: unknown
route: no guarded cheap path selected
decision: action=escalate outcome=FULL_COMPUTE_WITH_VALIDATOR; reason=risk=high forces FULL_COMPUTE_WITH_VALIDATOR
```