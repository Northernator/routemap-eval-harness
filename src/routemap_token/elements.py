"""Semantic 'element' tagger + codon motif scoring.

A deterministic, inference-only map from a token to one of ~33 functional
ELEMENTS (the "periodic table" layer), plus a 3-token codon motif scorer (the
"DNA" layer). No gold answer/evidence is ever consulted -- routing stays no-leak,
exactly like the token prior.

This is the element router's tagging layer, folded into routemap_token so the
`router_mode="element"` default has no dependency on the experimental package.
"""

from __future__ import annotations

import re

# --- element lexicons (closed classes; checked in priority order) ------------
NEGATION = {"not", "no", "never", "without", "cannot", "n't", "neither", "nor", "none"}
MODAL = {"must", "shall", "should", "may", "might", "can", "could", "will", "would",
         "required", "mandatory", "obligatory", "permitted", "allowed"}
CONDITION = {"if", "unless", "when", "where", "whenever", "provided", "assuming", "until", "once"}
EXCEPTION = {"except", "only", "but", "however", "although", "though", "despite", "whereas", "yet"}
REQUIRE = {"require", "requires", "required", "need", "needs", "depends", "depend", "necessitate", "entails"}
DEFINE = {"means", "defined", "defines", "define", "refers", "denotes", "describes", "constitutes"}
CAUSE = {"cause", "causes", "caused", "leads", "lead", "results", "result", "because",
         "therefore", "thus", "hence", "due", "enables", "produces"}
SUPPORT = {"supports", "support", "confirms", "shows", "demonstrates", "indicates",
           "according", "evidences", "establishes"}
CONTRADICT = {"contradicts", "refutes", "disputes", "conflicts", "contrary", "contradict"}
MAPSTO = {"maps", "links", "relates", "corresponds", "associated", "connects", "linked", "mapped"}
THRESHOLD_WORDS = {"least", "most", "minimum", "maximum", "exceeds", "exceed", "below", "above",
                   "greater", "less", "fewer", "more", "min", "max"}
SOURCE = {"according", "per", "source", "cited", "cites", "reference", "references", "citing"}
EXAMPLE = {"example", "examples", "instance", "including", "include", "includes", "namely"}
RISK = {"risk", "risks", "unsafe", "harm", "harmful", "threat", "threats", "vulnerability",
        "vulnerable", "danger", "dangerous", "attack", "malicious", "breach", "failure",
        "fail", "fails", "exploit", "abuse", "unauthorized", "adversarial"}
LIMITATION = {"limitation", "limitations", "caveat", "constraint", "constraints", "nonetheless",
              "nevertheless", "drawback", "restricted"}
PROBABILITY = {"likely", "probably", "possibly", "uncertain", "approximately", "roughly",
               "estimated", "potential", "potentially", "presumably"}
INSTRUCT = {"return", "write", "compute", "summarize", "choose", "list", "explain", "show",
            "compare", "provide", "describe", "identify", "ensure", "verify"}
SEQUENCE = {"then", "next", "first", "second", "third", "finally", "subsequently", "afterwards", "before", "after"}
CONNECTOR = {"and", "or", "also", "plus", "as", "well"}
SYSTEM = {"system", "systems", "model", "models", "framework", "frameworks", "policy", "policies",
          "protocol", "protocols", "standard", "standards", "guideline", "guidelines", "act",
          "regulation", "regulations", "law", "rule", "rules", "control", "controls", "process"}
ACTION_VERBS = {"approve", "approved", "review", "reviewed", "deploy", "deployed", "assess",
                "assessed", "evaluate", "evaluated", "test", "tested", "validate", "validated",
                "monitor", "monitored", "implement", "implemented", "classify", "detect",
                "detected", "generate", "generated", "process", "processed", "mitigate",
                "document", "report", "reported", "audit", "audited", "manage", "track"}
FUNCTION_WORDS = {"a", "an", "the", "of", "to", "in", "on", "by", "for", "with", "at", "is",
                  "are", "was", "were", "be", "been", "being", "it", "its", "that", "this",
                  "these", "those", "from", "into", "their", "they", "them", "which", "who",
                  "whom", "whose", "there", "here", "such", "any", "all", "each", "some"}

# Each element's base routing weight (0..1). High = likely important to keep.
ELEMENT_WEIGHT: dict[str, float] = {
    "NEGATION": 0.90, "MODAL": 0.80, "CONDITION": 0.74, "EXCEPTION": 0.52,
    "REQUIRE": 0.82, "DEFINE": 0.80, "CAUSE": 0.70, "SUPPORT": 0.68,
    "CONTRADICT": 0.80, "MAPSTO": 0.62,
    "NUMBER": 0.78, "DATE": 0.80, "THRESHOLD": 0.82, "UNIT": 0.66,
    "CITATION": 0.74, "SOURCE": 0.66, "EXAMPLE": 0.48, "QUOTE": 0.58,
    "ENTITY": 0.80, "SYSTEM": 0.74, "CONCEPT": 0.60, "ACTION": 0.66,
    "RISK": 0.86, "LIMITATION": 0.78, "PROBABILITY": 0.54,
    "INSTRUCT": 0.70, "CODE": 0.88, "FORMULA": 0.82,
    "SEQUENCE": 0.34, "CONNECTOR": 0.16, "FUNCTION": 0.10,
    "BOUNDARY": 0.05, "UNKNOWN": 0.45,
}

CODE_TOKENS = {"def", "import", "return", "class", "==", "!=", "{", "}", ";", "=>", "->", "(", ")"}


def classify_element(token: str) -> str:
    """Map a token to one functional element (deterministic, no-leak)."""
    value = str(token)
    lower = value.lower()
    base = lower.strip(".,;:!?\"'()[]")

    # structural / regex-detectable first
    if value in CODE_TOKENS or lower in CODE_TOKENS:
        return "CODE"
    if re.fullmatch(r"\W+", value):
        return "BOUNDARY"
    if re.fullmatch(r"\[\d+\]|https?://\S+", value):
        return "CITATION"
    if value in {'"', "'"}:
        return "QUOTE"
    if re.fullmatch(r"(19|20)\d{2}", value):
        return "DATE"
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
        return "NUMBER"
    if value in {"%"} or base in {"percent", "kg", "mb", "gb", "ms"}:
        return "UNIT"
    if re.search(r"[\^=/*_<>]|[A-Za-z]+\(\d*\)", value):
        return "FORMULA"
    if base in {">=", "<=", ">", "<"}:
        return "THRESHOLD"

    # closed-class lexicons (priority order: control > relation > risk > ...)
    if base in NEGATION:
        return "NEGATION"
    if base in MODAL:
        return "MODAL"
    if base in CONDITION:
        return "CONDITION"
    if base in REQUIRE:
        return "REQUIRE"
    if base in DEFINE:
        return "DEFINE"
    if base in CONTRADICT:
        return "CONTRADICT"
    if base in CAUSE:
        return "CAUSE"
    if base in SUPPORT:
        return "SUPPORT"
    if base in MAPSTO:
        return "MAPSTO"
    if base in THRESHOLD_WORDS:
        return "THRESHOLD"
    if base in RISK:
        return "RISK"
    if base in LIMITATION:
        return "LIMITATION"
    if base in PROBABILITY:
        return "PROBABILITY"
    if base in INSTRUCT:
        return "INSTRUCT"
    if base in SOURCE:
        return "SOURCE"
    if base in EXAMPLE:
        return "EXAMPLE"
    if base in EXCEPTION:
        return "EXCEPTION"
    if base in SEQUENCE:
        return "SEQUENCE"
    if base in SYSTEM:
        return "SYSTEM"
    if base in ACTION_VERBS:
        return "ACTION"
    if base in CONNECTOR:
        return "CONNECTOR"
    if base in FUNCTION_WORDS:
        return "FUNCTION"

    # open-class fallbacks
    if value[:1].isupper() and re.search(r"[A-Za-z]", value):
        return "ENTITY"
    if re.search(r"(ing|ed|ate|ise|ize|ifies|ify)$", base) and len(base) > 4:
        return "ACTION"
    if re.search(r"[A-Za-z]", value):
        return "CONCEPT"
    return "UNKNOWN"


# --- codon motif scoring ------------------------------------------------------
_CONTENTFUL = {"ENTITY", "SYSTEM", "CONCEPT", "ACTION", "NUMBER", "DATE", "RISK", "FORMULA"}
_OPERATOR = {"NEGATION", "MODAL", "REQUIRE", "CONDITION", "DEFINE", "CAUSE", "CONTRADICT",
             "THRESHOLD", "SUPPORT", "MAPSTO"}
_WEAK = {"FUNCTION", "BOUNDARY", "CONNECTOR", "SEQUENCE", "EXCEPTION", "EXAMPLE"}


def codon_value(elements: tuple[str, str, str]) -> float:
    """Score a 3-element codon for load-bearing structure (0..1)."""
    a, b, c = elements
    s = set(elements)
    operators = s & _OPERATOR
    contentful = s & _CONTENTFUL
    weak = s & _WEAK

    if (s & {"NEGATION", "MODAL"}) and not contentful and (weak or s <= (_WEAK | {"NEGATION", "MODAL", "PROBABILITY"})):
        return 0.12
    if s <= _WEAK:
        return 0.05

    if operators and contentful:
        val = 0.72
        if {"NEGATION", "MODAL"} & operators and {"ACTION", "REQUIRE", "RISK"} & s:
            val = 0.92  # prohibition / obligation / safety constraint
        if "THRESHOLD" in s and ("NUMBER" in s or "UNIT" in s):
            val = 0.90  # numeric threshold
        if "DEFINE" in s and contentful:
            val = 0.88  # definition
        if "RISK" in s:
            val = max(val, 0.88)
        return val

    if len(contentful) >= 2:
        return 0.66
    if contentful:
        return 0.5
    return 0.3


def best_codon_value(element_seq: list[str], index: int) -> float:
    """Max codon value over the (up to 3) trigrams covering position `index`."""
    n = len(element_seq)
    best = 0.0
    for start in (index - 2, index - 1, index):
        if 0 <= start and start + 2 < n:
            best = max(best, codon_value((element_seq[start], element_seq[start + 1], element_seq[start + 2])))
        elif 0 <= start < n:
            trip = tuple((element_seq[start + k] if start + k < n else "BOUNDARY") for k in range(3))
            best = max(best, codon_value(trip))
    return best


__all__ = ["classify_element", "ELEMENT_WEIGHT", "codon_value", "best_codon_value"]
