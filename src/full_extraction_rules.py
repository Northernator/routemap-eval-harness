NEGATED_PATTERNS = [
    "cannot",
    "does not",
    "do not",
    "not sufficient",
    "not a complete",
    "does not replace",
    "does not mean",
    "not by itself",
    "not settle",
]

LIMITED_PATTERNS = [
    "limitation",
    "difficult",
    "caveat",
    "residual",
    "partial",
    "incomplete",
    "constrained",
    "contextual",
    "delayed",
    "distributed",
    "may overestimate",
    "still required",
    "still needed",
]

ENTITY_PATTERNS = [
    ("nist", "NIST AI RMF"),
    ("ai risk management framework", "NIST AI RMF"),
    ("ncsc", "NCSC secure AI guidance"),
    ("secure ai system development", "secure AI development"),
    ("owasp", "OWASP LLM Top 10"),
    ("llm top 10", "OWASP LLM Top 10"),
    ("ico", "ICO AI guidance"),
    ("data protection", "data protection"),
    ("privacy", "data protection"),
    ("google", "Google SAIF"),
    ("saif", "Google SAIF"),
    ("microsoft", "Microsoft Responsible AI Standard"),
    ("responsible ai", "responsible AI"),
    ("cisa", "CISA AI roadmap"),
    ("ai roadmap", "AI roadmap"),
    ("eu ai act", "EU AI Act"),
    ("high-risk ai", "high-risk AI"),
    ("routemap", "RouteMap"),
    ("route extraction", "RouteMap"),
    ("route-based", "RouteMap"),
    ("route label", "RouteMap"),
    ("prompt injection", "prompt injection"),
    ("tool", "tool risk"),
    ("plugin", "tool risk"),
    ("risk management", "risk management"),
    ("risk", "AI risk"),
    ("ai system", "AI systems"),
    ("ai systems", "AI systems"),
    ("retrieval", "retrieval"),
    ("benchmark", "benchmark"),
    ("agent memory", "agent memory"),
    ("memory", "agent memory"),
    ("long-context", "long-context systems"),
    ("governance", "governance"),
    ("measurement", "measurement"),
    ("monitoring", "monitoring"),
    ("human oversight", "human oversight"),
    ("fairness", "fairness"),
    ("transparency", "transparency"),
    ("model", "model behavior"),
    ("data", "data"),
]


def clean_role_heading(text):
    stripped = "" if text is None else str(text).strip()
    for role in [
        "BACKGROUND",
        "CLAIM",
        "DEFINE",
        "METHOD",
        "RESULT",
        "LIMITATION",
        "NEXT_STEP",
        "EXAMPLE",
    ]:
        heading = f"### {role}"
        if stripped.startswith(heading):
            return stripped[len(heading):].strip()
    return stripped


def contains_any(text, patterns):
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def is_pure_title_or_metadata(text):
    stripped = "" if text is None else str(text).strip()
    return (
        stripped.startswith("# ")
        or stripped.startswith("## Source Metadata")
        or "Primary URL:" in stripped
        or "PDF URL:" in stripped
        or "Benchmark note:" in stripped
    )


def infer_operative_status(role, text):
    cleaned = clean_role_heading(text)
    if role in {"BACKGROUND", "DEFINE", "RESULT", "EXAMPLE"}:
        return "DESCRIPTIVE"
    if role == "NEXT_STEP":
        return "ACTIVE"
    if role == "METHOD":
        return "ACTIVE"
    if role == "LIMITATION":
        if contains_any(cleaned, NEGATED_PATTERNS):
            return "NEGATED"
        return "LIMITED"
    if role == "CLAIM":
        if contains_any(cleaned, NEGATED_PATTERNS):
            return "NEGATED"
        return "ACTIVE"
    return "DESCRIPTIVE"


def infer_relation(role, text):
    cleaned = clean_role_heading(text)
    lowered = cleaned.lower()
    if role == "BACKGROUND":
        return "sets_context"
    if role == "DEFINE":
        return "defines"
    if role == "METHOD":
        if "map" in lowered:
            return "maps_to"
        if "require" in lowered or "obligation" in lowered:
            return "requires"
        return "recommends"
    if role == "RESULT":
        if "retrieval" in lowered:
            return "supports_retrieval"
        return "reports_usefulness"
    if role == "LIMITATION":
        if contains_any(cleaned, NEGATED_PATTERNS):
            return "limits"
        return "warns_about"
    if role == "NEXT_STEP":
        return "proposes_next_test"
    if role == "EXAMPLE":
        return "gives_example"
    if role == "CLAIM":
        return "asserts"
    return "asserts"


def infer_answer_relevant(role, text):
    if role == "BACKGROUND":
        return "NO" if is_pure_title_or_metadata(text) else "MAYBE"
    return "YES"


def extract_entities(text, title=""):
    haystack = f"{title} {clean_role_heading(text)}".lower()
    entities = []
    seen = set()
    for pattern, entity in ENTITY_PATTERNS:
        if pattern in haystack and entity not in seen:
            entities.append(entity)
            seen.add(entity)
    if not entities:
        entities.append("RouteMap segment")
    return "; ".join(entities[:8])


def infer_full_fields(role, text, title=""):
    return {
        "entities": extract_entities(text, title),
        "operative_status": infer_operative_status(role, text),
        "relation": infer_relation(role, text),
        "answer_relevant": infer_answer_relevant(role, text),
    }
