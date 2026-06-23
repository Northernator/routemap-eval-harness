ALLOWED_FINE_ROLES = [
    "BACKGROUND",
    "CLAIM",
    "DEFINE",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
]

TAXONOMIES = {
    "fine_8": {role: role for role in ALLOWED_FINE_ROLES},
    "coarse_5": {
        "BACKGROUND": "CONTEXT",
        "CLAIM": "ASSERTION",
        "DEFINE": "ASSERTION",
        "RESULT": "ASSERTION",
        "METHOD": "ACTION",
        "NEXT_STEP": "ACTION",
        "LIMITATION": "CAVEAT",
        "EXAMPLE": "INSTANCE",
    },
    "coarse_4": {
        "BACKGROUND": "CONTEXT",
        "CLAIM": "CONTENT",
        "DEFINE": "CONTENT",
        "RESULT": "CONTENT",
        "METHOD": "ACTION",
        "NEXT_STEP": "ACTION",
        "EXAMPLE": "ACTION",
        "LIMITATION": "CAVEAT",
    },
    "coarse_3": {
        "BACKGROUND": "CONTEXT",
        "CLAIM": "SUBSTANTIVE",
        "DEFINE": "SUBSTANTIVE",
        "METHOD": "SUBSTANTIVE",
        "RESULT": "SUBSTANTIVE",
        "NEXT_STEP": "SUBSTANTIVE",
        "EXAMPLE": "SUBSTANTIVE",
        "LIMITATION": "CAVEAT",
    },
}


def map_role(role: str, taxonomy: str) -> str:
    if taxonomy not in TAXONOMIES:
        raise KeyError(f"Unknown taxonomy: {taxonomy}")
    if role not in TAXONOMIES[taxonomy]:
        raise KeyError(f"Unknown role for {taxonomy}: {role}")
    return TAXONOMIES[taxonomy][role]


def available_taxonomies() -> list[str]:
    return list(TAXONOMIES)
