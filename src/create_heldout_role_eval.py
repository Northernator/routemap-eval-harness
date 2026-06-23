import argparse
import csv
from collections import Counter
from pathlib import Path


ROLES = [
    "BACKGROUND",
    "CLAIM",
    "DEFINE",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
]

COLUMNS = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "notes",
]

FORBIDDEN_HEADINGS = [
    "### DEFINE",
    "### METHOD",
    "### RESULT",
    "### LIMITATION",
    "### NEXT_STEP",
    "### EXAMPLE",
    "### CLAIM",
    "### BACKGROUND",
]

ROWS = [
    {
        "title": "heldout_ai_risk_sources.md",
        "text": "The OECD AI principles page gives policy context for trustworthy AI and names common public-interest concerns.",
        "gold_role": "BACKGROUND",
        "notes": "Source context",
    },
    {
        "title": "heldout_secure_ai_release_notes.md",
        "text": "A vendor white paper describes the setting for secure model release reviews and explains why release evidence is collected.",
        "gold_role": "BACKGROUND",
        "notes": "Source context",
    },
    {
        "title": "heldout_llm_security_sources.md",
        "text": "This source summarizes common LLM application security issues for readers who need document-level context before annotation.",
        "gold_role": "BACKGROUND",
        "notes": "Source context",
    },
    {
        "title": "heldout_nist_profile_notes.md",
        "text": "NIST's profile document provides background for connecting AI risk management language to procurement and assurance workflows.",
        "gold_role": "BACKGROUND",
        "notes": "Framework context",
    },
    {
        "title": "heldout_owasp_update_notes.md",
        "text": "OWASP maintains a project hub where prompt injection, model behavior, and application controls are discussed together.",
        "gold_role": "BACKGROUND",
        "notes": "Project context",
    },
    {
        "title": "heldout_privacy_guidance_notes.md",
        "text": "The ICO guidance explains how data protection concepts frame AI design decisions before a system is deployed.",
        "gold_role": "BACKGROUND",
        "notes": "Guidance context",
    },
    {
        "title": "heldout_eu_ai_act_notes.md",
        "text": "The EU AI Act places high-risk systems within a regulatory setting that includes documentation, testing, and post-market duties.",
        "gold_role": "BACKGROUND",
        "notes": "Regulatory context",
    },
    {
        "title": "heldout_route_benchmark_notes.md",
        "text": "A route-extraction benchmark package contains source notes, gold labels, evaluation scripts, and mismatch review files.",
        "gold_role": "BACKGROUND",
        "notes": "Dataset context",
    },
    {
        "title": "heldout_agent_memory_notes.md",
        "text": "The project README records why long-context memory needs both raw source access and compact route pointers.",
        "gold_role": "BACKGROUND",
        "notes": "Document context",
    },
    {
        "title": "heldout_cisa_roadmap_notes.md",
        "text": "A CISA briefing introduces AI roadmap language for critical infrastructure and cyber defence audiences.",
        "gold_role": "BACKGROUND",
        "notes": "Source context",
    },
    {
        "title": "heldout_ai_risk_claims.md",
        "text": "Monitoring is valuable, but it should be treated as an accountability signal rather than proof of safety.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_risk_route_claims.md",
        "text": "Risk scores are more useful when their route through data, model behavior, and user impact remains visible.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_governance_claims.md",
        "text": "A governance process can become theatre if the evidence never reaches release decisions.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_secure_ai_claims.md",
        "text": "Secure AI work is stronger when control evidence travels with retrieval results instead of living in a separate checklist.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_memory_claims.md",
        "text": "Agent memory should prioritize dependency structure over recency alone when a task depends on hidden state.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_privacy_claims.md",
        "text": "Privacy review cannot be reduced to checkbox language even when a formal process exists.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_retrieval_claims.md",
        "text": "Route-based retrieval should help most when a question requires relation context rather than repeated keywords.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_model_card_claims.md",
        "text": "A model card is most valuable when it explains design choices rather than simply listing controls.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_eval_claims.md",
        "text": "Safety evaluation needs traceable disagreement, not just a single-number score.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_context_claims.md",
        "text": "Retrieval quality depends on whether relevant segments are connected, not merely present in the context window.",
        "gold_role": "CLAIM",
        "notes": "General thesis",
    },
    {
        "title": "heldout_route_definitions.md",
        "text": "Route provenance names the chain of sources, roles, and relations that support an answer.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_trace_definitions.md",
        "text": "A retrieval trace is the ordered path from query intent to selected evidence and final answer support.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_posture_definitions.md",
        "text": "AI risk posture denotes the current exposure created by model capability, deployment context, controls, and oversight.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_privacy_definitions.md",
        "text": "A consent boundary describes where a user permission applies, expires, or must be renewed.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_safety_case_definitions.md",
        "text": "A safety case is an argument that links system hazards, mitigations, evidence, and residual uncertainty.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_graph_definitions.md",
        "text": "A dependency edge names a relationship where one passage changes the interpretation or reliability of another passage.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_eval_definitions.md",
        "text": "An evaluation blind spot refers to a recurring failure that the benchmark does not make observable.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_ops_definitions.md",
        "text": "Operational readiness means the team can monitor, update, and roll back an AI feature under expected conditions.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_redteam_definitions.md",
        "text": "A red-team finding records a tested weakness, the attempted exploit route, and the observed system response.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_context_definitions.md",
        "text": "Context collapse describes the loss of task-relevant structure when many passages are merged into one prompt.",
        "gold_role": "DEFINE",
        "notes": "Defines a term",
    },
    {
        "title": "heldout_annotation_methods.md",
        "text": "Start by mapping the user question to candidate roles, then retrieve passages that fill each role before composing the answer.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_security_methods.md",
        "text": "The security reviewer should identify tool permissions, untrusted inputs, output handling, and logging gaps before approval.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_testing_methods.md",
        "text": "Run canary prompts against the retrieval stack, inspect the selected segments, and record any unsupported answer claims.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_eval_methods.md",
        "text": "For each query, retrieve candidates with both route labels and keyword fallback, then compare the ranked evidence sets.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_deployment_methods.md",
        "text": "A deployment workflow should consider model version, data source freshness, human escalation, and rollback criteria.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_review_methods.md",
        "text": "Operators compare the generated answer with source segments and flag any claim that lacks a supporting route.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_two_pass_methods.md",
        "text": "Use a two-pass review: first assign passage roles, then verify whether the answer used the right role sequence.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_procedure_methods.md",
        "text": "The procedure records the query, route candidates, accepted evidence, rejected evidence, and reviewer rationale.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_annotation_methods.md",
        "text": "During annotation, a reviewer marks the main role first and adds relation notes only after the role label is stable.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_monitoring_methods.md",
        "text": "A monitoring routine samples live answers, checks source drift, and opens review tickets for unsupported routes.",
        "gold_role": "METHOD",
        "notes": "Procedure",
    },
    {
        "title": "heldout_pilot_results.md",
        "text": "The pilot run found that route labels recovered five answer-relevant passages missed by keyword search.",
        "gold_role": "RESULT",
        "notes": "Reported finding",
    },
    {
        "title": "heldout_split_results.md",
        "text": "The held-out split produced a balanced confusion table with most errors concentrated in claim versus method.",
        "gold_role": "RESULT",
        "notes": "Reported finding",
    },
    {
        "title": "heldout_annotation_results.md",
        "text": "The annotation pass yielded ten examples per role and exposed disagreement around benchmark setup rows.",
        "gold_role": "RESULT",
        "notes": "Reported finding",
    },
    {
        "title": "heldout_index_results.md",
        "text": "A route index reduced review time in the sandbox because assessors could jump directly to supporting passages.",
        "gold_role": "RESULT",
        "notes": "Reported finding",
    },
    {
        "title": "heldout_classifier_results.md",
        "text": "The classifier matched all title rows but missed several definition rows that lacked obvious trigger words.",
        "gold_role": "RESULT",
        "notes": "Reported finding",
    },
    {
        "title": "heldout_review_results.md",
        "text": "Human review showed that privacy examples were easier to identify than abstract governance claims.",
        "gold_role": "RESULT",
        "notes": "Reported finding",
    },
    {
        "title": "heldout_document_results.md",
        "text": "This document is useful for retrieval because it separates source context, process advice, and caveats.",
        "gold_role": "RESULT",
        "notes": "Reported usefulness",
    },
    {
        "title": "heldout_error_results.md",
        "text": "The held-out sample exposed overreliance on the word process as a method cue.",
        "gold_role": "RESULT",
        "notes": "Reported finding",
    },
    {
        "title": "heldout_log_results.md",
        "text": "Evaluation logs showed higher recall when route edges were kept with the selected text.",
        "gold_role": "RESULT",
        "notes": "Reported finding",
    },
    {
        "title": "heldout_report_results.md",
        "text": "The retrieval report marked the no-leak condition as a harder test than the heading-aware condition.",
        "gold_role": "RESULT",
        "notes": "Reported finding",
    },
    {
        "title": "heldout_safety_limitations.md",
        "text": "The audit method does not by itself prove that a deployed model is safe under new user behavior.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_domain_limitations.md",
        "text": "A benchmark built from one policy domain can overstate performance on operational incident reports.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_privacy_limitations.md",
        "text": "Consent signals may be absent, stale, or too broad to justify a specific downstream model use.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_measurement_limitations.md",
        "text": "Risk labels remain difficult when harms are delayed, distributed across actors, or visible only after deployment.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_synthetic_limitations.md",
        "text": "Synthetic passages can hide retrieval weaknesses because their structure is cleaner than production documentation.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_monitoring_limitations.md",
        "text": "Model monitoring does not replace adversarial testing, source inspection, or incident response planning.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_threat_limitations.md",
        "text": "A top-ten risk list is not a complete threat model for every sector, product, or deployment path.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_sample_limitations.md",
        "text": "Small gold sets leave uncertainty about whether the classifier learned roles or memorized document style.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_route_limitations.md",
        "text": "Route compression can lose detail when relation labels are correct but entity boundaries are wrong.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_judging_limitations.md",
        "text": "The evaluator cannot judge whether an answer is socially acceptable when the gold file only records retrieval relevance.",
        "gold_role": "LIMITATION",
        "notes": "Caveat/constraint",
    },
    {
        "title": "heldout_future_eval_steps.md",
        "text": "Future work should add passages from incident reports, procurement checklists, and model release notes.",
        "gold_role": "NEXT_STEP",
        "notes": "Future evaluation action",
    },
    {
        "title": "heldout_next_split_steps.md",
        "text": "The next benchmark version should reserve unseen documents before tuning any role classifier.",
        "gold_role": "NEXT_STEP",
        "notes": "Future evaluation action",
    },
    {
        "title": "heldout_routemap_steps.md",
        "text": "RouteMap should test whether the classifier still works when titles and section labels are removed.",
        "gold_role": "NEXT_STEP",
        "notes": "Future evaluation action",
    },
    {
        "title": "heldout_review_steps.md",
        "text": "Reviewers should next compare v3 errors with human disagreement rather than only counting exact matches.",
        "gold_role": "NEXT_STEP",
        "notes": "Recommended follow-up",
    },
    {
        "title": "heldout_system_steps.md",
        "text": "A practical implementation should combine route labels, embeddings, lexical search, and explicit abstention.",
        "gold_role": "NEXT_STEP",
        "notes": "Future implementation action",
    },
    {
        "title": "heldout_adversarial_steps.md",
        "text": "Add adversarial passages that mention risk and process while serving as claims or background context.",
        "gold_role": "NEXT_STEP",
        "notes": "Future evaluation action",
    },
    {
        "title": "heldout_metric_steps.md",
        "text": "The next evaluation should measure whether role errors change final answer correctness.",
        "gold_role": "NEXT_STEP",
        "notes": "Future evaluation action",
    },
    {
        "title": "heldout_privacy_steps.md",
        "text": "Future work should separate privacy definitions from examples involving consent failures.",
        "gold_role": "NEXT_STEP",
        "notes": "Future evaluation action",
    },
    {
        "title": "heldout_split_steps.md",
        "text": "Build a second held-out split with documents from domains that were not used during rule design.",
        "gold_role": "NEXT_STEP",
        "notes": "Future evaluation action",
    },
    {
        "title": "heldout_adjudication_steps.md",
        "text": "Re-run the classifier after labels are adjudicated and archive both the old and new mismatch files.",
        "gold_role": "NEXT_STEP",
        "notes": "Recommended follow-up",
    },
    {
        "title": "heldout_healthcare_examples.md",
        "text": "A hospital model that ranks patients for follow-up illustrates how privacy, safety, and triage evidence can overlap.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
    {
        "title": "heldout_prompt_examples.md",
        "text": "Prompt injection in a support ticket can redirect an agent from refund policy to credential exfiltration.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
    {
        "title": "heldout_finance_examples.md",
        "text": "A model that predicts loan churn from transaction history gives a concrete privacy and fairness review case.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
    {
        "title": "heldout_coding_examples.md",
        "text": "A coding agent may retrieve a permission check, a route handler, and a migration before editing an authorization path.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
    {
        "title": "heldout_poisoning_examples.md",
        "text": "A data poisoning scenario could insert false safety claims into a retrieval corpus before model evaluation.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
    {
        "title": "heldout_reviewer_examples.md",
        "text": "A reviewer asking which controls failed can require one limitation passage and one incident timeline passage.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
    {
        "title": "heldout_passage_examples.md",
        "text": "A passage that compares two monitoring practices can serve as an example even when it contains procedural language.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
    {
        "title": "heldout_hiring_examples.md",
        "text": "A model used to screen job applicants may need separate routes for bias evidence, appeal process, and audit logs.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
    {
        "title": "heldout_privacy_examples.md",
        "text": "A privacy officer checking a chatbot transcript might trace user consent, retained context, and deletion obligations.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
    {
        "title": "heldout_question_examples.md",
        "text": "A question asking why a release was blocked may need a result row, a limitation row, and a next-action row.",
        "gold_role": "EXAMPLE",
        "notes": "Concrete scenario",
    },
]


def with_segment_ids(rows):
    return [
        {"segment_id": f"HELDOUT_S{index:04d}", **row}
        for index, row in enumerate(rows, start=1)
    ]


def validate(rows):
    if len(rows) != 80:
        raise ValueError(f"expected 80 rows, found {len(rows)}")

    counts = Counter(row["gold_role"] for row in rows)
    for role in ROLES:
        if counts[role] != 10:
            raise ValueError(f"expected 10 {role} rows, found {counts[role]}")

    segment_ids = [row["segment_id"] for row in rows]
    if len(segment_ids) != len(set(segment_ids)):
        raise ValueError("segment_id values are not unique")

    for row in rows:
        text = row["text"]
        for heading in FORBIDDEN_HEADINGS:
            if heading in text:
                raise ValueError(f"forbidden heading {heading!r} in {row['segment_id']}")


def write_csv(output_path):
    rows = with_segment_ids(ROWS)
    validate(rows)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = write_csv(args.out)
    print(f"Wrote {len(rows)} rows to {args.out}")
    counts = Counter(row["gold_role"] for row in rows)
    print("Count by gold_role:")
    for role in ROLES:
        print(f"- {role}: {counts[role]}")


if __name__ == "__main__":
    main()
