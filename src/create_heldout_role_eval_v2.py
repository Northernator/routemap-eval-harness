import csv
from pathlib import Path


OUT_PATH = Path("data/v1/gold/heldout_role_eval_v2.csv")
FORBIDDEN_HEADINGS = [
    "### BACKGROUND",
    "### CLAIM",
    "### DEFINE",
    "### METHOD",
    "### RESULT",
    "### LIMITATION",
    "### NEXT_STEP",
    "### EXAMPLE",
]

ROWS = [
    ("fresh_policy_context_notes.md", "A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric exercise.", "BACKGROUND", "Policy context"),
    ("fresh_release_archive_notes.md", "The release archive describes why model approval packets include evidence logs, reviewer notes, and unresolved caveats.", "BACKGROUND", "Archive context"),
    ("fresh_privacy_handbook_notes.md", "The privacy handbook gives consent examples before turning to any RouteMap annotation task.", "BACKGROUND", "Guidance context"),
    ("fresh_trace_manual_notes.md", "A documentation page introduces retrieval trace diagrams for teams that have never used route labels.", "BACKGROUND", "Document context"),
    ("fresh_memory_brief_notes.md", "An agent memory briefing mentions risk, benchmark drift, and long-context failures while setting document scope.", "BACKGROUND", "Briefing context"),
    ("fresh_tool_security_notes.md", "The tool-use security note records common permission-check vocabulary used by incident responders.", "BACKGROUND", "Vocabulary context"),
    ("fresh_benchmark_package_notes.md", "A benchmark design appendix lists source context, gold labels, and mismatch review artifacts for auditors.", "BACKGROUND", "Dataset context"),
    ("fresh_evidence_selection_notes.md", "The evidence selection primer explains how policy context can affect which passages are useful to reviewers.", "BACKGROUND", "Primer context"),
    ("fresh_governance_catalog_notes.md", "A model release governance catalog summarizes approval roles, audit trails, and release-board terminology.", "BACKGROUND", "Catalog context"),
    ("fresh_incident_response_notes.md", "An incident response playbook provides background on escalation records without recommending a new classifier.", "BACKGROUND", "Playbook context"),
    ("fresh_eval_claims.md", "AI safety evaluation becomes more credible when disagreement remains traceable instead of hidden behind an average.", "CLAIM", "Thesis"),
    ("fresh_release_claims.md", "Model release governance should treat missing evidence as a decision risk, not as harmless paperwork.", "CLAIM", "Thesis"),
    ("fresh_consent_claims.md", "Consent boundaries lose force when downstream permission checks are invisible to the answer composer.", "CLAIM", "Thesis"),
    ("fresh_trace_claims.md", "A retrieval trace matters because answer support depends on the path, not merely on a cited passage.", "CLAIM", "Thesis"),
    ("fresh_memory_claims.md", "Agent memory can amplify stale assumptions when route provenance is absent from recall.", "CLAIM", "Thesis"),
    ("fresh_controls_claims.md", "Controls that never travel with retrieved evidence rarely change practical review behaviour.", "CLAIM", "Thesis"),
    ("fresh_benchmark_claims.md", "Benchmark design is weaker when easy source context outnumbers adversarial route segments.", "CLAIM", "Thesis"),
    ("fresh_human_review_claims.md", "Human review adds value only if reviewers can inspect the evidence selection path.", "CLAIM", "Thesis"),
    ("fresh_tool_claims.md", "Tool-use security depends on permission boundaries being checked at the moment of action.", "CLAIM", "Thesis"),
    ("fresh_audit_claims.md", "An audit trail without answer support is evidence of activity rather than evidence of reliability.", "CLAIM", "Thesis"),
    ("fresh_route_terms.md", "Route provenance: the documented lineage connecting source context, selected evidence, and answer support.", "DEFINE", "Definition"),
    ("fresh_trace_terms.md", "Retrieval trace names the visible sequence from question intent through evidence selection to final response.", "DEFINE", "Definition"),
    ("fresh_consent_terms.md", "Consent boundary covers the point at which a permission grant stops applying to a new use.", "DEFINE", "Definition"),
    ("fresh_release_terms.md", "Model release governance denotes the approval practice linking evaluation findings to launch decisions.", "DEFINE", "Definition"),
    ("fresh_memory_terms.md", "Agent memory routing describes choosing stored context by dependency rather than by freshness alone.", "DEFINE", "Definition"),
    ("fresh_segment_terms.md", "A route segment label marks the job a passage performs inside a larger retrieval chain.", "DEFINE", "Definition"),
    ("fresh_support_terms.md", "Answer support refers to evidence that directly justifies a response rather than merely sharing keywords.", "DEFINE", "Definition"),
    ("fresh_audit_terms.md", "Audit trail, in this setting, names records that let reviewers reconstruct a release or retrieval decision.", "DEFINE", "Definition"),
    ("fresh_control_terms.md", "Control surface labels the places where safeguards can change model, tool, or data behaviour.", "DEFINE", "Definition"),
    ("fresh_review_terms.md", "Human-review checkpoint names a decision point where automated evidence must be inspected before action.", "DEFINE", "Definition"),
    ("fresh_eval_methods.md", "Compare each generated answer against its retrieval trace, then flag unsupported assertions for review.", "METHOD", "Procedure"),
    ("fresh_release_methods.md", "Before launch, collect release evidence, unresolved limitations, and reviewer sign-off in one packet.", "METHOD", "Procedure"),
    ("fresh_privacy_methods.md", "Map consent records to permission checks before selecting evidence for a privacy-sensitive answer.", "METHOD", "Procedure"),
    ("fresh_memory_methods.md", "Rank memory candidates by route dependency, source age, and whether the task needs hidden state.", "METHOD", "Procedure"),
    ("fresh_tool_methods.md", "Log tool calls with permission scope, selected route segment, and the reason the action was allowed.", "METHOD", "Procedure"),
    ("fresh_incident_methods.md", "During an incident review, connect symptoms to retrieval traces and then to the control that failed.", "METHOD", "Procedure"),
    ("fresh_benchmark_methods.md", "Sample benchmark rows from policy context, operational procedures, examples, and caveats in equal measure.", "METHOD", "Procedure"),
    ("fresh_human_review_methods.md", "Route uncertain answers to human review when evidence selection conflicts with the final answer.", "METHOD", "Procedure"),
    ("fresh_audit_methods.md", "Store audit trail entries beside answer support so later reviewers can reproduce the decision.", "METHOD", "Procedure"),
    ("fresh_annotation_methods.md", "Label the passage role first, record relation evidence second, and adjudicate entity boundaries last.", "METHOD", "Procedure"),
    ("fresh_trace_results.md", "The evaluation run recovered more answer-support passages after route provenance was kept with the snippets.", "RESULT", "Observed outcome"),
    ("fresh_release_results.md", "Release reviewers resolved blocked decisions faster when caveats appeared beside the evidence packet.", "RESULT", "Observed outcome"),
    ("fresh_privacy_results.md", "The consent-boundary cases produced fewer false positives once permission checks were separated from general privacy text.", "RESULT", "Observed outcome"),
    ("fresh_memory_results.md", "Memory routing returned older but more relevant context for tasks with hidden state dependencies.", "RESULT", "Observed outcome"),
    ("fresh_tool_results.md", "Tool-use security review found that missing permission logs explained most rejected actions.", "RESULT", "Observed outcome"),
    ("fresh_benchmark_results.md", "A mixed benchmark split exposed brittle behaviour on examples that looked like procedures.", "RESULT", "Observed outcome"),
    ("fresh_human_review_results.md", "Human reviewers agreed more often when the retrieval trace displayed rejected evidence as well as accepted evidence.", "RESULT", "Observed outcome"),
    ("fresh_audit_results.md", "Audit trail inspection showed that answer support was present in seven of nine release decisions.", "RESULT", "Observed outcome"),
    ("fresh_selection_results.md", "Evidence selection improved after source context was grouped by route segment instead of document order.", "RESULT", "Observed outcome"),
    ("fresh_error_results.md", "The mismatch review revealed that policy-context rows were often confused with broad claims.", "RESULT", "Observed outcome"),
    ("fresh_eval_limits.md", "Future benchmark rounds may still overstate generalisation if they reuse the same policy vocabulary.", "LIMITATION", "Caveat"),
    ("fresh_release_limits.md", "A complete release packet does not prove that the deployed model will behave safely after integration.", "LIMITATION", "Caveat"),
    ("fresh_consent_limits.md", "Consent records can be too stale to justify a fresh tool action even when the interface looks authorized.", "LIMITATION", "Caveat"),
    ("fresh_trace_limits.md", "Retrieval traces may miss reasoning steps that occur after evidence enters the prompt.", "LIMITATION", "Caveat"),
    ("fresh_memory_limits.md", "Agent memory can preserve obsolete source context unless review processes remove or downgrade it.", "LIMITATION", "Caveat"),
    ("fresh_tool_limits.md", "Permission checks are not enough when the tool output can leak private data through a later route.", "LIMITATION", "Caveat"),
    ("fresh_review_limits.md", "Human review is constrained when audit trails omit rejected evidence and reviewer rationale.", "LIMITATION", "Caveat"),
    ("fresh_benchmark_limits.md", "A route benchmark remains incomplete without operational incidents, adversarial examples, and noisy documentation.", "LIMITATION", "Caveat"),
    ("fresh_policy_limits.md", "Policy context can warn about risk without specifying the control step needed for a particular system.", "LIMITATION", "Caveat"),
    ("fresh_support_limits.md", "Answer support is fragile if relation labels are right but entity boundaries drift across passages.", "LIMITATION", "Caveat"),
    ("fresh_eval_steps.md", "Next, assemble a second fresh split from incident reports and release-board minutes.", "NEXT_STEP", "Future work"),
    ("fresh_release_steps.md", "Future evaluation should compare model release governance rows with ordinary project-management notes.", "NEXT_STEP", "Future work"),
    ("fresh_privacy_steps.md", "Add consent-boundary examples that mix permission checks with unrelated privacy background.", "NEXT_STEP", "Future work"),
    ("fresh_trace_steps.md", "The next retrieval test should hide titles and require the extractor to infer route provenance from text alone.", "NEXT_STEP", "Future work"),
    ("fresh_memory_steps.md", "Run an agent-memory benchmark where old context competes with newer but less relevant evidence.", "NEXT_STEP", "Future work"),
    ("fresh_tool_steps.md", "A follow-up tool-use security set should include plugins, command execution, and delegated agents.", "NEXT_STEP", "Future work"),
    ("fresh_review_steps.md", "Evaluate whether human review changes final answers when rejected evidence is shown.", "NEXT_STEP", "Future work"),
    ("fresh_benchmark_steps.md", "Build noisy benchmark rows that contain definitions, caveats, and examples in a single paragraph.", "NEXT_STEP", "Future work"),
    ("fresh_audit_steps.md", "The next audit-trail test should measure whether reviewers can reconstruct the release decision.", "NEXT_STEP", "Future work"),
    ("fresh_support_steps.md", "Create answer-support cases where the cited passage is relevant but the relation path is wrong.", "NEXT_STEP", "Future work"),
    ("fresh_hospital_examples.md", "In a hospital triage review, consent evidence and safety evaluation notes can point to different routes.", "EXAMPLE", "Concrete scenario"),
    ("fresh_release_examples.md", "Suppose a release board blocks launch because the audit trail lacks reviewer rationale.", "EXAMPLE", "Concrete scenario"),
    ("fresh_chatbot_examples.md", "When a support chatbot requests a refund-tool call, the permission boundary may depend on account history.", "EXAMPLE", "Concrete scenario"),
    ("fresh_memory_examples.md", "One coding task may need last week's migration note rather than the newest design comment.", "EXAMPLE", "Concrete scenario"),
    ("fresh_trace_examples.md", "For instance, a cited paragraph can mention privacy while failing to support the answer's consent claim.", "EXAMPLE", "Concrete scenario"),
    ("fresh_tool_examples.md", "A plugin that reads calendars and sends email illustrates why tool-use security needs separate route checks.", "EXAMPLE", "Concrete scenario"),
    ("fresh_incident_examples.md", "During an incident, an operator might trace a harmful answer through retrieval logs and a stale memory entry.", "EXAMPLE", "Concrete scenario"),
    ("fresh_benchmark_examples.md", "A synthetic benchmark row could look procedural while actually describing a concrete reviewer scenario.", "EXAMPLE", "Concrete scenario"),
    ("fresh_audit_examples.md", "An auditor comparing two release packets may follow evidence selection differences before reading conclusions.", "EXAMPLE", "Concrete scenario"),
    ("fresh_answer_examples.md", "A final answer that cites policy context but omits the controlling route segment shows a support failure.", "EXAMPLE", "Concrete scenario"),
]


def heading_count(rows):
    return sum(1 for _, text, _, _ in rows for heading in FORBIDDEN_HEADINGS if heading in text)


def build_rows():
    rows = []
    for index, (title, text, role, notes) in enumerate(ROWS, start=1):
        rows.append({
            "segment_id": f"HELDOUT2_S{index:04d}",
            "title": title,
            "text": text,
            "gold_role": role,
            "notes": notes,
        })
    return rows


def main():
    rows = build_rows()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["segment_id", "title", "text", "gold_role", "notes"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Rows written: {len(rows)}")
    print(f"Forbidden heading count: {heading_count(ROWS)}")
    print(f"Wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
