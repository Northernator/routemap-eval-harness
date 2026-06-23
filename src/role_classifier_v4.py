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
    "The OECD",
    "A vendor white paper",
    "NIST's profile document",
    "A route-extraction benchmark package contains",
    "The project README records",
    "A CISA briefing introduces",
    "A source note",
    "A guidance page",
    "A policy document",
    "A benchmark package",
    "This source",
    "The ICO guidance explains",
    "OWASP maintains",
    "The EU AI Act",
]

BACKGROUND_CONTAINS = [
    "provides background",
    "gives policy context",
    "describes the setting",
    "introduces",
    "records why",
    "document-level context",
    "regulatory setting",
    "source notes",
    "source/document/context",
]

DEFINE_STARTS = [
    "A retrieval trace is",
    "Route provenance names",
    "AI risk posture denotes",
    "A consent boundary describes",
    "A permission boundary",
    "A route segment",
    "A control surface",
    "A human-review checkpoint",
    "A safety case is",
    "A dependency edge names",
    "Operational readiness means",
    "A red-team finding records",
    "Context collapse describes",
]

DEFINE_CONTAINS = [
    "names the chain",
    "is the ordered path",
    "denotes the current exposure",
    "describes where",
    " means ",
    "refers to",
    "is a term for",
    "is a label for",
    "is the point where",
    "defines",
    " is an argument that ",
    " names a relationship where ",
    " records a tested weakness",
    " describes the loss of ",
]

RESULT_STARTS = [
    "The run shows",
    "The evaluation shows",
    "The test shows",
    "The score indicates",
    "The result suggests",
    "The mismatch review shows",
    "The benchmark exposes",
    "The extractor correctly",
    "The system recovered",
    "The report records",
    "The output demonstrates",
    "The pilot run found",
    "The held-out split produced",
    "The annotation pass yielded",
    "A route index reduced",
    "The classifier matched",
    "Human review showed",
    "This document is useful",
    "The held-out sample exposed",
    "Evaluation logs showed",
    "The retrieval report marked",
]

RESULT_CONTAINS = [
    "the run shows",
    "the evaluation shows",
    "the test shows",
    "the score indicates",
    "the result suggests",
    "the mismatch review shows",
    "the benchmark exposes",
    "the extractor correctly",
    "the system recovered",
    " accuracy",
    " jaccard",
    "mismatch count",
    "the report records",
    "the output demonstrates",
    " found that ",
    " produced a balanced ",
    " yielded ",
    " reduced review time ",
    " showed that ",
    " logs showed ",
    " exposed overreliance ",
    " marked the ",
]

NEXT_STEP_STARTS = [
    "Future work should",
    "The next benchmark",
    "The next evaluation",
    "RouteMap should test",
    "Reviewers should next",
    "A practical implementation should",
    "Add adversarial",
    "Build a second",
    "Re-run the classifier",
    "A follow-up",
    "The next version",
]

NEXT_STEP_CONTAINS = [
    " next ",
    "future ",
    "should be added",
    "should be evaluated",
    "should be tested",
    "should compare",
    "should include",
    "should run",
    "the next benchmark",
    "a follow-up",
    "the next version",
    "future corpora",
    "reserve unseen documents",
    "before tuning",
]

EXAMPLE_STARTS = [
    "For example",
    "In one scenario",
    "A user",
    "A developer",
    "A model that",
    "A model used",
    "A coding agent",
    "An auditor",
    "A reviewer",
    "A tenant",
    "A vendor",
    "A prompt injection",
    "Prompt injection",
    "A data poisoning",
    "A retrieval failure",
    "A passage",
    "An application",
    "A hospital model",
    "A privacy officer",
    "A question",
]

EXAMPLE_CONTAINS = [
    "such as",
    "for instance",
    "when a user ",
    "when a developer ",
    "when a model ",
    "when an agent ",
    "when a reviewer ",
    "when a tenant ",
    "when a vendor ",
    "when a prompt ",
    "when a data ",
    "when a retrieval ",
    "when a passage ",
    "when an application ",
    "where a ",
    " illustrates how ",
    " gives a concrete ",
    " can serve as an example",
]

LIMITATION_CONTAINS = [
    "does not",
    "cannot",
    "is insufficient",
    "is not enough",
    "may miss",
    "may overestimate",
    "may fail",
    "may be absent",
    "can overstate",
    "can hide",
    "can lose",
    "unless",
    "without",
    "residual risk",
    "constraint",
    "blind spot",
    "ambiguous",
    "adversarial",
    "not a substitute",
    "not complete",
    "not a complete",
    "remain difficult",
    "remains difficult",
    "leave uncertainty",
    "wrong",
    "too broad to justify",
]

METHOD_STARTS = [
    "Start by",
    "Run canary",
    "For each query",
    "Operators compare",
    "Use a two-pass",
    "During annotation",
]

METHOD_CONTAINS = [
    "should identify",
    "should label",
    "should log",
    "should store",
    "should retrieve",
    "should compare",
    "can store",
    "can retrieve",
    " uses ",
    " use ",
    "combines",
    " runs ",
    " run ",
    " maps ",
    "mapping",
    " checks ",
    " check ",
    "validates",
    "review process",
    "workflow",
    "procedure",
    "implementation",
    "control step",
    "retrieve candidates",
    "record any unsupported",
    "records the query",
    "marks the main role",
    "samples live answers",
    "opens review tickets",
]


def _clean(text: str) -> str:
    stripped = "" if text is None else str(text).strip()
    for role in ALLOWED_ROLES:
        heading = f"### {role}"
        if stripped.startswith(heading):
            return stripped[len(heading):].strip()
    return stripped


def _starts_with_any(text: str, patterns: list[str]) -> bool:
    return any(text.startswith(pattern) for pattern in patterns)


def _contains_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def _is_title_or_metadata(text: str) -> bool:
    return (
        text.startswith("# ")
        or text.startswith("## Source Metadata")
        or "Primary URL:" in text
        or "PDF URL:" in text
        or "Benchmark note:" in text
    )


def _is_dataset_insufficiency(text: str) -> bool:
    lowered = text.lower()
    return (
        "insufficient" in lowered
        or "not enough" in lowered
        or "may overestimate" in lowered
        or "overestimate performance" in lowered
        or "current dataset" in lowered
    )


def classify_role_v4(text: str, title: str = "") -> str:
    del title
    stripped = _clean(text)
    if not stripped:
        return "BACKGROUND"
    if _is_title_or_metadata(stripped):
        return "BACKGROUND"

    if _starts_with_any(stripped, BACKGROUND_STARTS) or _contains_any(stripped, BACKGROUND_CONTAINS):
        return "BACKGROUND"
    if _starts_with_any(stripped, DEFINE_STARTS) or _contains_any(stripped, DEFINE_CONTAINS):
        return "DEFINE"
    if _starts_with_any(stripped, RESULT_STARTS) or _contains_any(stripped, RESULT_CONTAINS):
        return "RESULT"
    if _contains_any(stripped, NEXT_STEP_CONTAINS) or _starts_with_any(stripped, NEXT_STEP_STARTS):
        if _is_dataset_insufficiency(stripped):
            return "LIMITATION"
        return "NEXT_STEP"
    if _starts_with_any(stripped, EXAMPLE_STARTS) or _contains_any(stripped, EXAMPLE_CONTAINS):
        return "EXAMPLE"
    if _contains_any(stripped, LIMITATION_CONTAINS):
        return "LIMITATION"
    if _starts_with_any(stripped, METHOD_STARTS) or _contains_any(stripped, METHOD_CONTAINS):
        return "METHOD"
    return "CLAIM"
