# Entity Ontology V1

This ontology defines canonical RouteMap v1 entity labels for the entity-only benchmark. Matching should be conservative: emit a canonical entity only when the text or title gives a domain-specific signal, not when it contains a generic word that could apply anywhere.

| canonical entity | synonyms / trigger phrases | do not emit when |
|---|---|---|
| AI safety evaluation | AI safety evaluation; safety evaluation; safety eval; model safety evaluation | The row only mentions generic evaluation without AI safety context. |
| AI risk management | AI risk management; AI RMF; AI risk posture; AI risk governance; managing AI risk | The row only says risk or risk governance without AI-specific wording. |
| answer support | answer support; final answer support; evidence support; support route; unsupported answer | The row only uses support as a generic verb. |
| agent memory | agent memory; long-context memory; memory routing; memory trace; memory briefing | The row only says memory outside an agent or retrieval-routing context. |
| audit trail | audit trail; audit trails; audit log; audit record; traceable record; approval record | The row only says audit as a generic role name without records or traceability. |
| benchmark | benchmark; benchmark design; benchmark package; corpus; corpora; held-out; test set; boundary-pair test | The row only mentions a one-off example, not an evaluation dataset. |
| consent boundary | consent boundary; consent; consent check; consent state; consent examples | The row only mentions permission or authorization without consent. |
| controls | controls; control; mitigation; mitigations; guardrail; safeguard; safety control | The row only says control as a generic verb. |
| data protection | data protection; personal data; protected data; data-handling; data handling | The row only says data and privacy is not the topic. |
| evidence selection | evidence selection; selected evidence; evidence choice; evidence logs; source selection; passage selection | The row only mentions evidence as a general noun. |
| evaluation | evaluation; evaluator; eval; score; accuracy; metric; scoring; measured; measurement | The row is only about a benchmark package without performance measurement. |
| gold labels | gold label; gold labels; annotation label; annotation labels; adjudicated label; label set | The row only uses label as a verb outside annotation. |
| governance | governance; oversight; accountability; approval board; release board; institutional process | The row only says process without governance or oversight. |
| human review | human review; reviewer; reviewers; auditor; auditors; manual review; human checkpoint; release-board reviewer | The row only says user or developer without review responsibility. |
| incident response | incident response; incident responder; incident responders; escalation; escalation record; response playbook | The row only mentions risk without operational response. |
| LLM application security | LLM application security; LLM security; prompt injection; tool risk; plugin risk; application security | The row only mentions general security outside LLM/tool-use context. |
| mismatch review | mismatch review; mismatch; mismatches; error analysis; failure pattern; disagreement review | The row only says disagreement as a social process without review or errors. |
| model release governance | model release governance; model approval; approval packet; release archive; release review; model release; release gate | The row only says governance unrelated to model release. |
| permission boundary | permission boundary; permission check; permissions; authorization; authorisation; access boundary; access check | The row only says consent without authorization or access control. |
| policy context | policy context; policy overview; policy document; policy framing; guidance page; regulatory context | The row only uses policy as an internal implementation option. |
| privacy | privacy; private; personal privacy; privacy handbook | The row is specifically about data protection rather than privacy rights or privacy framing. |
| retrieval | retrieval; retrieve; retrieved; evidence retrieval; evidence selection; retrieval failure | The row only says selected evidence without retrieval process. |
| retrieval trace | retrieval trace; retrieval traces; trace diagram; trace diagrams; retrieved path; retrieval path | The row only mentions traceability or audit trails without retrieval. |
| risk management | risk management; risk governance; risk posture; risk register; risk process | The row only says risk as a generic adjective. |
| route extraction | route extraction; route-extraction; route-aware extraction; extract routes; route labelling; route labeling | The row only mentions RouteMap as a project name. |
| route provenance | route provenance; provenance chain; source-to-answer chain; provenance record; provenance path | The row only mentions source context without provenance. |
| RouteMap | RouteMap; route-aware; RouteMap-oriented | The row only uses route as a generic path metaphor. |
| RouteMap segment | RouteMap segment; route segment; segment; passage; route passage; route label; route labels; route edge; route edges | The row only mentions segment in a non-RouteMap context. |
| secure AI development | secure AI development; secure AI; security review; secure model; secure model development | The row only mentions security as general application security. |
| source context | source context; source note; source notes; source package; background note; document scope; context note | The row only says source as a citation without contextual framing. |
| tool-use security | tool-use security; tool use security; tool risk; plugin risk; permission-check vocabulary; tool invocation | The row only mentions tools as a generic workflow aid. |

Use this ontology for baseline extraction only. It is not final evidence of robust entity understanding.
