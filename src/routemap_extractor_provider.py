import re
from pathlib import Path

from entity_ontology_v1 import extract_entities_ontology_v1, split_entity_set
from role_classifier_v4 import classify_role_v4
from routemap_extraction_contract import empty_extraction, normalize_extraction


PROMPT_TEMPLATE_PATH = Path("data/v1/gold/ROUTEMAP_LLM_EXTRACTION_PROMPT_TEMPLATE.md")
RELATION_BY_ROLE = {
    "BACKGROUND": "sets_context",
    "DEFINE": "defines",
    "CLAIM": "asserts",
    "METHOD": "recommends",
    "RESULT": "reports_usefulness",
    "LIMITATION": "limits",
    "NEXT_STEP": "proposes_next_test",
    "EXAMPLE": "gives_example",
}
NEGATION_RE = re.compile(r"\b(cannot|can't|does not|do not|insufficient|not enough|not complete|fails?|failure|unable)\b")
METADATA_RE = re.compile(r"\b(source|package|project|readme|appendix|overview|briefing|handbook|catalog|playbook|metadata)\b")


class RouteMapExtractorProvider:
    def extract(self, text: str, title: str = "") -> dict:
        raise NotImplementedError


class StubProvider(RouteMapExtractorProvider):
    def extract(self, text: str, title: str = "") -> dict:
        result = empty_extraction()
        result["rationale"] = "Stub provider default extraction."
        return result


def operative_status(role: str, text: str) -> str:
    lowered = (text or "").lower()
    if role in {"BACKGROUND", "DEFINE", "RESULT", "EXAMPLE"}:
        return "DESCRIPTIVE"
    if role in {"METHOD", "NEXT_STEP"}:
        return "ACTIVE"
    if role == "LIMITATION":
        return "NEGATED" if NEGATION_RE.search(lowered) else "LIMITED"
    if role == "CLAIM":
        return "NEGATED" if NEGATION_RE.search(lowered) else "ACTIVE"
    return "DESCRIPTIVE"


def answer_relevant(role: str, text: str, title: str = "") -> str:
    if role != "BACKGROUND":
        return "YES"
    return "NO" if METADATA_RE.search(f"{title or ''} {text or ''}".lower()) else "MAYBE"


class RuleProvider(RouteMapExtractorProvider):
    def extract(self, text: str, title: str = "") -> dict:
        role = classify_role_v4(text, title)
        entities = sorted(split_entity_set(extract_entities_ontology_v1(text, title)))
        return normalize_extraction({
            "role": role,
            "entities": entities,
            "operative_status": operative_status(role, text),
            "relation": RELATION_BY_ROLE.get(role, "asserts"),
            "answer_relevant": answer_relevant(role, text, title),
            "rationale": "Offline rule provider using role_classifier_v4 plus entity ontology v1.",
        })


class PromptOnlyProvider(RouteMapExtractorProvider):
    def build_prompt(self, text: str, title: str = "") -> str:
        template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
        return f"{template}\n\nTitle: {title}\nText: {text}\nOutput JSON:"

    def extract(self, text: str, title: str = "") -> dict:
        result = empty_extraction()
        result["rationale"] = self.build_prompt(text, title)
        return result


def make_provider(name: str) -> RouteMapExtractorProvider:
    if name == "stub":
        return StubProvider()
    if name == "rule":
        return RuleProvider()
    if name == "prompt_only":
        return PromptOnlyProvider()
    raise ValueError(f"Unknown provider: {name}")
