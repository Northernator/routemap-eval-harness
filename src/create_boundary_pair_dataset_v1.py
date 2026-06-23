import csv
from pathlib import Path


OUT_PATH = Path("data/v1/gold/boundary_pair_role_eval_v1.csv")
FORBIDDEN_HEADINGS = [
    "### CLAIM",
    "### DEFINE",
    "### METHOD",
    "### RESULT",
    "### LIMITATION",
    "### NEXT_STEP",
    "### EXAMPLE",
    "### BACKGROUND",
]

BOUNDARY_PAIRS = [
    ("CLAIM_vs_DEFINE", "CLAIM", "DEFINE"),
    ("RESULT_vs_CLAIM", "RESULT", "CLAIM"),
    ("BACKGROUND_vs_CLAIM", "BACKGROUND", "CLAIM"),
    ("BACKGROUND_vs_EXAMPLE", "BACKGROUND", "EXAMPLE"),
    ("BACKGROUND_vs_RESULT", "BACKGROUND", "RESULT"),
    ("METHOD_vs_EXAMPLE", "METHOD", "EXAMPLE"),
    ("RESULT_vs_METHOD", "RESULT", "METHOD"),
    ("CLAIM_vs_METHOD", "CLAIM", "METHOD"),
]

TOPICS = [
    "AI risk management",
    "RouteMap route extraction",
    "retrieval trace",
    "route provenance",
    "source context",
    "benchmark evaluation",
    "model release governance",
    "privacy",
    "consent boundary",
    "permission boundary",
    "human review",
    "incident response",
    "tool-use security",
    "agent memory",
    "answer support",
    "evidence selection",
    "audit trail",
    "data protection",
    "secure AI development",
    "route segment",
]

DIFFICULTIES = ["MEDIUM", "HARD", "HARD", "MEDIUM", "HARD"]


def definition_text(topic, index):
    forms = [
        f"{topic} names the boundary that determines which evidence can support a RouteMap answer.",
        f"{topic} denotes the route function linking source context, reviewer judgement, and answer support.",
        f"In this benchmark, {topic} refers to the labelled concept that separates route evidence from adjacent context.",
        f"{topic} covers the identity of a route step rather than an argument about whether the step is useful.",
        f"{topic} is the term used for the dependency surface that reviewers must recognise before classification.",
    ]
    return forms[index % len(forms)]


def claim_text(topic, index):
    forms = [
        f"{topic} matters most when hidden route assumptions can change the final answer.",
        f"Reliable RouteMap extraction depends on making {topic} visible before reviewers trust a response.",
        f"{topic} becomes fragile when evidence selection is separated from human review.",
        f"Route-aware systems should treat {topic} as a substantive risk signal, not as decoration.",
        f"{topic} can mislead evaluators when the route path is absent from the audit trail.",
    ]
    return forms[index % len(forms)]


def result_text(topic, index):
    forms = [
        f"The benchmark evaluation found that {topic} rows were recovered more often after route provenance was shown.",
        f"The mismatch review showed that {topic} created the largest cluster of role errors.",
        f"The held-out run produced fewer unsupported answers when {topic} stayed attached to selected evidence.",
        f"The audit report recorded that {topic} improved reviewer agreement on difficult route segments.",
        f"The extractor output marked {topic} correctly in most source-context examples but missed harder variants.",
    ]
    return forms[index % len(forms)]


def background_text(topic, index):
    forms = [
        f"A source note introduces {topic} vocabulary for readers before any route labels are assigned.",
        f"The benchmark package includes {topic} examples as context for later annotation work.",
        f"A project README describes why {topic} appears in the route extraction corpus.",
        f"The policy briefing summarizes {topic} concerns without asking reviewers to choose a procedure.",
        f"A documentation page gives background on {topic} for teams comparing source context and answer support.",
    ]
    return forms[index % len(forms)]


def method_text(topic, index):
    forms = [
        f"Compare the selected passage with {topic}, then record whether the answer has direct support.",
        f"Log {topic} beside each route segment before the reviewer approves the final response.",
        f"Map {topic} to the permission boundary and then inspect any unsupported claims.",
        f"During review, retrieve {topic} evidence first and adjudicate relation labels second.",
        f"Store {topic} notes with the audit trail so later reviewers can reproduce the decision.",
    ]
    return forms[index % len(forms)]


def example_text(topic, index):
    forms = [
        f"In one release-board case, {topic} caused a reviewer to block launch until answer support was visible.",
        f"A support chatbot using {topic} may request a tool action before the consent boundary is checked.",
        f"An incident responder tracing {topic} might follow retrieval logs back to stale agent memory.",
        f"For instance, a route segment about {topic} can look procedural while only illustrating a reviewer scenario.",
        f"A privacy review involving {topic} shows how evidence selection and human review can overlap.",
    ]
    return forms[index % len(forms)]


ROLE_TEXT = {
    "BACKGROUND": background_text,
    "CLAIM": claim_text,
    "DEFINE": definition_text,
    "METHOD": method_text,
    "RESULT": result_text,
    "EXAMPLE": example_text,
}

ROLE_NOTES = {
    "BACKGROUND": "Source context, not substantive claim.",
    "CLAIM": "Argues thesis rather than defining or reporting output.",
    "DEFINE": "Defines term boundary rather than arguing thesis.",
    "METHOD": "Reusable procedure, not concrete scenario.",
    "RESULT": "Reports evaluation outcome, not general claim.",
    "EXAMPLE": "Concrete scenario, not reusable procedure.",
}


def role_counts_for_pair(first_role, second_role):
    return [(first_role, 13), (second_role, 12)]


def build_rows():
    rows = []
    counter = 1
    for boundary_pair, first_role, second_role in BOUNDARY_PAIRS:
        for role, count in role_counts_for_pair(first_role, second_role):
            contrast = second_role if role == first_role else first_role
            for local_index in range(count):
                topic = TOPICS[(counter + local_index) % len(TOPICS)]
                text = ROLE_TEXT[role](topic, local_index)
                rows.append({
                    "boundary_pair": boundary_pair,
                    "segment_id": f"BOUNDARY_S{counter:04d}",
                    "title": f"boundary_{boundary_pair.lower()}_{counter:04d}.md",
                    "text": text,
                    "gold_role": role,
                    "contrast_role": contrast,
                    "difficulty": DIFFICULTIES[(counter + local_index) % len(DIFFICULTIES)],
                    "notes": ROLE_NOTES[role],
                })
                counter += 1
    return rows


def main():
    rows = build_rows()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["boundary_pair", "segment_id", "title", "text", "gold_role", "contrast_role", "difficulty", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)
    forbidden_count = sum(
        1 for row in rows for heading in FORBIDDEN_HEADINGS if heading in row["text"]
    )
    print(f"Rows written: {len(rows)}")
    print(f"Forbidden heading count: {forbidden_count}")
    print(f"Wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
