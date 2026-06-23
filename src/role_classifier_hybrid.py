from role_classifier_v3 import classify_role_v3


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
    "### CLAIM": "CLAIM",
    "### DEFINE": "DEFINE",
    "### METHOD": "METHOD",
    "### RESULT": "RESULT",
    "### LIMITATION": "LIMITATION",
    "### NEXT_STEP": "NEXT_STEP",
    "### EXAMPLE": "EXAMPLE",
}


def classify_role_hybrid(text: str, title: str = "") -> str:
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

    return classify_role_v3(text, title)
