import re


CANONICAL_ENTITIES = [
    "AI safety evaluation",
    "AI risk management",
    "answer support",
    "agent memory",
    "audit trail",
    "benchmark",
    "consent boundary",
    "controls",
    "data protection",
    "evidence selection",
    "evaluation",
    "gold labels",
    "governance",
    "human review",
    "incident response",
    "LLM application security",
    "mismatch review",
    "model release governance",
    "permission boundary",
    "policy context",
    "privacy",
    "retrieval",
    "retrieval trace",
    "risk management",
    "route extraction",
    "route provenance",
    "RouteMap",
    "RouteMap segment",
    "secure AI development",
    "source context",
    "tool-use security",
]

ENTITY_SYNONYMS = {
    "AI safety evaluation": [
        "ai safety evaluation",
        "safety evaluation",
        "safety eval",
        "model safety evaluation",
    ],
    "AI risk management": [
        "ai risk management",
        "ai rmf",
        "ai risk posture",
        "ai risk governance",
        "managing ai risk",
    ],
    "answer support": [
        "answer support",
        "final answer support",
        "evidence support",
        "support route",
        "unsupported answer",
    ],
    "agent memory": [
        "agent memory",
        "long-context memory",
        "long context memory",
        "memory routing",
        "memory trace",
        "memory briefing",
    ],
    "audit trail": [
        "audit trail",
        "audit trails",
        "audit log",
        "audit record",
        "approval record",
        "traceable record",
        "traceable",
    ],
    "benchmark": [
        "benchmark",
        "benchmark design",
        "benchmark package",
        "corpus",
        "corpora",
        "held-out",
        "held out",
        "test set",
        "boundary-pair test",
        "boundary pair test",
    ],
    "consent boundary": [
        "consent boundary",
        "consent",
        "consent check",
        "consent state",
        "consent examples",
    ],
    "controls": [
        "controls",
        "control",
        "mitigation",
        "mitigations",
        "guardrail",
        "guardrails",
        "safeguard",
        "safeguards",
        "safety control",
    ],
    "data protection": [
        "data protection",
        "personal data",
        "protected data",
        "data-handling",
        "data handling",
    ],
    "evidence selection": [
        "evidence selection",
        "selected evidence",
        "evidence choice",
        "evidence choices",
        "evidence logs",
        "evidence log",
        "source selection",
        "passage selection",
    ],
    "evaluation": [
        "evaluation",
        "evaluator",
        "evaluators",
        "eval",
        "score",
        "scores",
        "scoring",
        "accuracy",
        "metric",
        "metrics",
        "measured",
        "measurement",
    ],
    "gold labels": [
        "gold label",
        "gold labels",
        "annotation label",
        "annotation labels",
        "adjudicated label",
        "adjudicated labels",
        "label set",
        "label sets",
    ],
    "governance": [
        "governance",
        "oversight",
        "accountability",
        "approval board",
        "release board",
        "institutional process",
    ],
    "human review": [
        "human review",
        "reviewer",
        "reviewers",
        "auditor",
        "auditors",
        "manual review",
        "human checkpoint",
        "release-board reviewer",
        "release board reviewer",
    ],
    "incident response": [
        "incident response",
        "incident responder",
        "incident responders",
        "escalation",
        "escalation record",
        "response playbook",
    ],
    "LLM application security": [
        "llm application security",
        "llm security",
        "prompt injection",
        "tool risk",
        "plugin risk",
        "application security",
    ],
    "mismatch review": [
        "mismatch review",
        "mismatch",
        "mismatches",
        "error analysis",
        "failure pattern",
        "failure patterns",
        "disagreement review",
    ],
    "model release governance": [
        "model release governance",
        "model approval",
        "approval packet",
        "approval packets",
        "release archive",
        "release review",
        "release reviews",
        "model release",
        "release gate",
    ],
    "permission boundary": [
        "permission boundary",
        "permission check",
        "permission checks",
        "permissions",
        "permission",
        "authorization",
        "authorisation",
        "access boundary",
        "access check",
    ],
    "policy context": [
        "policy context",
        "policy overview",
        "policy document",
        "policy framing",
        "guidance page",
        "regulatory context",
    ],
    "privacy": [
        "privacy",
        "private",
        "personal privacy",
        "privacy handbook",
    ],
    "retrieval": [
        "retrieval",
        "retrieve",
        "retrieved",
        "evidence retrieval",
        "retrieval failure",
    ],
    "retrieval trace": [
        "retrieval trace",
        "retrieval traces",
        "trace diagram",
        "trace diagrams",
        "retrieved path",
        "retrieval path",
    ],
    "risk management": [
        "risk management",
        "risk governance",
        "risk posture",
        "risk register",
        "risk process",
    ],
    "route extraction": [
        "route extraction",
        "route-extraction",
        "route-aware extraction",
        "extract routes",
        "route labelling",
        "route labeling",
    ],
    "route provenance": [
        "route provenance",
        "provenance chain",
        "source-to-answer chain",
        "source to answer chain",
        "provenance record",
        "provenance path",
    ],
    "RouteMap": [
        "routemap",
        "route-aware",
        "route aware",
        "routemap-oriented",
        "routemap oriented",
    ],
    "RouteMap segment": [
        "routemap segment",
        "route segment",
        "route segments",
        "segment",
        "segments",
        "passage",
        "passages",
        "route passage",
        "route passages",
        "route label",
        "route labels",
        "route edge",
        "route edges",
    ],
    "secure AI development": [
        "secure ai development",
        "secure ai",
        "security review",
        "secure model",
        "secure model development",
    ],
    "source context": [
        "source context",
        "source note",
        "source notes",
        "source package",
        "background note",
        "document scope",
        "context note",
    ],
    "tool-use security": [
        "tool-use security",
        "tool use security",
        "tool risk",
        "plugin risk",
        "permission-check vocabulary",
        "permission check vocabulary",
        "tool invocation",
    ],
}

NORMALIZED = {entity.lower(): entity for entity in CANONICAL_ENTITIES}
ORDER = {entity: index for index, entity in enumerate(CANONICAL_ENTITIES)}


def _clean(value: str) -> str:
    return "" if value is None else str(value).strip()


def _pattern(phrase: str) -> str:
    escaped = re.escape(phrase.lower()).replace("\\ ", r"[\s-]+")
    return rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"


def _contains(haystack: str, phrase: str) -> bool:
    return re.search(_pattern(phrase), haystack) is not None


def normalize_entity(entity: str) -> str:
    value = _clean(entity)
    if not value:
        return ""
    lowered = value.lower()
    if lowered in NORMALIZED:
        return NORMALIZED[lowered]
    for canonical, synonyms in ENTITY_SYNONYMS.items():
        if lowered == canonical.lower() or lowered in {synonym.lower() for synonym in synonyms}:
            return canonical
    return value


def split_entity_set(value: str) -> set[str]:
    entities = set()
    for part in (_clean(value)).split(";"):
        normalized = normalize_entity(part)
        if normalized:
            entities.add(normalized)
    return entities


def format_entity_set(entities: set[str]) -> str:
    return "; ".join(sorted(entities, key=lambda entity: (ORDER.get(entity, len(ORDER)), entity.lower())))


def extract_entities_ontology_v1(text: str, title: str = "") -> str:
    haystack = f"{_clean(title)} {_clean(text)}".lower()
    found = set()
    for canonical in CANONICAL_ENTITIES:
        phrases = [canonical] + ENTITY_SYNONYMS.get(canonical, [])
        if any(_contains(haystack, phrase) for phrase in phrases):
            found.add(canonical)

    if "data protection" in found:
        found.discard("data")
    if "AI risk management" in found:
        found.discard("AI risk")
    if "retrieval trace" in found:
        found.add("retrieval")
    if "route extraction" in found:
        found.add("RouteMap")
    if "RouteMap segment" in found:
        found.add("RouteMap")
    if "tool-use security" in found:
        found.add("LLM application security")

    return format_entity_set(found)
