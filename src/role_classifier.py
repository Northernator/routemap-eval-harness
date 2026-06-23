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


HEADING_ROLES = {
    "### BACKGROUND": "BACKGROUND",
    "### DEFINE": "DEFINE",
    "### METHOD": "METHOD",
    "### RESULT": "RESULT",
    "### LIMITATION": "LIMITATION",
    "### NEXT_STEP": "NEXT_STEP",
    "### EXAMPLE": "EXAMPLE",
    "### CLAIM": "CLAIM",
}


NEXT_STEP_KEYWORDS = [
    "should test",
    "next benchmark",
    "next step",
    "future work",
    "should include",
    "practical implementation should",
]

EXAMPLE_KEYWORDS = [
    "for example",
    "example",
    "scenario",
    "includes logging",
    "should be treated differently from",
]

DEFINE_KEYWORDS = [
    "is defined as",
    "refers to",
    "is the structured process",
    "is a set of",
    "includes information relating to",
    "is a vulnerability pattern",
]

METHOD_KEYWORDS = [
    "workflow",
    "procedure",
    "process",
    "lifecycle",
    "controls",
    "mitigation",
    "implementation",
    "monitoring",
    "assessment",
    "test whether",
]

RESULT_KEYWORDS = [
    "result",
    "useful because",
    "useful for retrieval",
    "should produce",
    "annotation should classify",
    "labels across",
]

LIMITATION_KEYWORDS = [
    "limitation",
    "cannot",
    "does not",
    "risk",
    "constraint",
    "gap",
    "challenge",
    "weakness",
    "may fail",
    "unless",
]


def contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def classify_role(text: str, title: str = "") -> str:
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
    ):
        return "BACKGROUND"

    for heading, role in HEADING_ROLES.items():
        if stripped.startswith(heading):
            return role

    lowered = stripped.lower()
    if contains_any(lowered, NEXT_STEP_KEYWORDS):
        return "NEXT_STEP"
    if contains_any(lowered, EXAMPLE_KEYWORDS):
        return "EXAMPLE"
    if contains_any(lowered, DEFINE_KEYWORDS):
        return "DEFINE"
    if contains_any(lowered, METHOD_KEYWORDS):
        return "METHOD"
    if contains_any(lowered, RESULT_KEYWORDS):
        return "RESULT"
    if contains_any(lowered, LIMITATION_KEYWORDS):
        return "LIMITATION"

    return "CLAIM"
