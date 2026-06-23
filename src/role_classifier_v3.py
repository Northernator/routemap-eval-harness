ALLOWED_ROLES = [
    "BACKGROUND",
    "CLAIM",
    "DEFINE",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
]


BACKGROUND_STARTS = [
    "NIST developed",
    "OWASP maintains",
    "The ICO guidance explains",
    "The NCSC guidance treats",
    "Google describes SAIF",
    "Google SAIF",
    "Microsoft",
    "CISA",
    "The EU AI Act",
    "This source",
    "This guidance",
    "This document contains",
    "A RouteMap benchmark needs documents that contain",
    "Long-context systems can fail",
]

DEFINE_STARTS = [
    "A responsible AI standard converts",
    "An AI roadmap is",
    "A risk management system",
    "Agent memory routing is",
    "Secure AI system development means",
]

DEFINE_CONTAINS = [
    " means ",
    " is a strategic plan ",
    " is a continuous process ",
    " is the process of ",
    " is the structured process ",
    " is a set of ",
    " is a vulnerability pattern ",
    " converts broad principles into ",
    " includes information relating to ",
    " refers to ",
    " describes the job a passage performs ",
]

RESULT_STARTS = [
    "This document is useful",
    "This document is especially useful",
    "This document is suitable",
    "This document should create labels",
    "This document should produce",
    "A RouteMap annotation should classify",
    "Previous sandbox tests showed",
    "A compact route index can reduce",
]

RESULT_CONTAINS = [
    "should produce RouteMap labels",
    "should create labels across",
    "is useful for retrieval",
    "is suitable for dependency-chain retrieval",
]

NEXT_STEP_STARTS = [
    "For a RouteMap benchmark, use this document to test",
    "For RouteMap, this source is useful for testing",
    "RouteMap should test whether",
    "The next benchmark version should",
    "A practical implementation should combine",
]

NEXT_STEP_CONTAINS = [
    "future work",
    "next benchmark",
    "next step",
]

EXAMPLE_STARTS = [
    "A model that ",
    "A model used ",
    "A coding agent ",
    "Prompt injection ",
    "A data poisoning scenario ",
    "A passage that ",
    "A question asking ",
    "A fairness review ",
    "Secure operation includes ",
]

EXAMPLE_CONTAINS = [
    "should be annotated as",
    "should be treated differently from",
]

LIMITATION_CONTAINS = [
    "does not by itself prove",
    "is not a complete",
    "does not replace",
    "does not mean all risks are eliminated",
    "may overestimate performance",
    "future corpora should include ambiguous and adversarial passages",
    "residual risk",
    "implementation evidence is still required",
    "not a complete threat model",
    "remains difficult",
    "does not settle",
    "external validation",
    "still needed",
    "sets direction, but",
    "can lose detail",
]

METHOD_CONTAINS = [
    "should identify",
    "should label each passage",
    "can store compact identifiers",
    "security review should identify",
    "human annotator should label",
    "workflow",
    "procedure",
    "implementation approach",
    "mitigation method",
    "can be operationalised",
    "can be routed through",
    "should consider",
    "should map assets",
    "can include impact assessment",
    "should identify known and foreseeable risks",
]

CLAIM_STARTS = [
    "AI risk is not only",
    "Security outcomes cannot be delegated entirely",
    "AI systems can create data protection risks because",
    "Principles alone are not sufficient unless",
    "Risk management is not a one-time document",
    "Route-based retrieval should be most useful",
    "Security for AI needs to be designed",
    "AI can improve cyber defence",
    "LLM security differs",
    "A memory system should not treat",
]


def starts_with_any(text, patterns):
    return any(text.startswith(pattern) for pattern in patterns)


def contains_any(text, patterns):
    return any(pattern in text for pattern in patterns)


def classify_role_v3(text: str, title: str = "") -> str:
    del title
    stripped = "" if text is None else str(text).strip()
    if not stripped:
        return "BACKGROUND"

    if stripped.startswith("# ") and not stripped.startswith("### "):
        return "BACKGROUND"

    if (
        stripped.startswith("## Source Metadata")
        or "Primary URL:" in stripped
        or "PDF URL:" in stripped
        or "Benchmark note:" in stripped
        or starts_with_any(stripped, BACKGROUND_STARTS)
    ):
        return "BACKGROUND"

    if starts_with_any(stripped, CLAIM_STARTS):
        return "CLAIM"

    lowered = stripped.lower()

    if starts_with_any(stripped, DEFINE_STARTS) or contains_any(lowered, DEFINE_CONTAINS):
        return "DEFINE"

    if starts_with_any(stripped, RESULT_STARTS) or contains_any(lowered, RESULT_CONTAINS):
        return "RESULT"

    if contains_any(
        lowered,
        [
            "may overestimate performance; future corpora should include",
            "future corpora should include ambiguous and adversarial passages",
        ],
    ):
        return "LIMITATION"

    if starts_with_any(stripped, NEXT_STEP_STARTS) or contains_any(lowered, NEXT_STEP_CONTAINS):
        return "NEXT_STEP"

    if starts_with_any(stripped, EXAMPLE_STARTS) or contains_any(lowered, EXAMPLE_CONTAINS):
        return "EXAMPLE"

    if contains_any(lowered, LIMITATION_CONTAINS):
        return "LIMITATION"

    if "unless" in lowered and (
        "not a complete" in lowered
        or "does not" in lowered
        or "cannot" in lowered
        or "still required" in lowered
    ):
        return "LIMITATION"

    if contains_any(lowered, METHOD_CONTAINS):
        return "METHOD"

    return "CLAIM"
