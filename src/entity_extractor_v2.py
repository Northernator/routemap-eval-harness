import re


ENTITY_PATTERNS = [
    ("EU AI Act", [r"\beu ai act\b"]),
    ("NIST AI RMF", [r"\bnist\b", r"\bai rmf\b"]),
    ("OWASP LLM Top 10", [r"\bowasp\b", r"\bllm top 10\b"]),
    ("ICO AI guidance", [r"\bico\b"]),
    ("AI principles", [r"\bai principles\b"]),
    ("trustworthy AI", [r"\btrustworthy ai\b"]),
    ("model release review", [r"\bmodel release review\b", r"\brelease reviews?\b"]),
    ("release evidence", [r"\brelease evidence\b"]),
    ("evaluation scripts", [r"\bevaluation scripts?\b"]),
    ("mismatch review", [r"\bmismatch review\b", r"\berror analysis\b", r"\bfailure pattern\b"]),
    ("gold labels", [r"\bgold labels?\b", r"\bannotation labels?\b"]),
    ("benchmark", [r"\bbenchmark\b", r"\bcorpus\b", r"\bcorpora\b", r"\bheld-out\b", r"\btest set\b", r"\bgold sets?\b"]),
    ("LLM application security", [r"\bllm application security\b", r"\bllm security\b", r"\bprompt injection\b", r"\btool risk\b", r"\bplugin risk\b"]),
    ("prompt injection", [r"\bprompt injection\b"]),
    ("secure AI development", [r"\bsecure ai\b", r"\bsecurity review\b", r"\bsecure model\b"]),
    ("high-risk AI", [r"\bhigh-risk ai\b", r"\bhigh risk setting\b", r"\bhigh-risk systems?\b"]),
    ("AI roadmap", [r"\bai roadmap\b"]),
    ("AI risk management", [r"\bai risk\b", r"\brisk management\b", r"\brisk posture\b"]),
    ("risk management", [r"\brisk management\b"]),
    ("privacy", [r"\bprivacy\b", r"\bprivate\b", r"\bpersonal data\b", r"\bconsent\b"]),
    ("data protection", [r"\bdata protection\b"]),
    ("permission boundary", [r"\bpermission\b", r"\bconsent boundary\b", r"\bauthori[sz]ation\b", r"\baccess boundary\b"]),
    ("human review", [r"\bhuman review\b", r"\breviewer\b", r"\breviewers\b", r"\bauditor\b", r"\bmanual review\b", r"\bhuman checkpoint\b", r"\bhuman escalation\b", r"\bhuman annotator\b"]),
    ("controls", [r"\bcontrols?\b", r"\bmitigations?\b", r"\bguardrails?\b", r"\bsafeguards?\b"]),
    ("retrieval trace", [r"\bretrieval trace\b"]),
    ("answer support", [r"\banswer support\b", r"\bfinal answer support\b", r"\bevidence support\b", r"\bsupporting route\b", r"\bunsupported answer claims?\b"]),
    ("retrieval", [r"\bretrieval\b", r"\bretrieve\b", r"\bretrieved\b", r"\bretrieves\b", r"\bevidence selection\b", r"\bkeyword search\b"]),
    ("source context", [r"\bsource notes?\b", r"\bsource context\b", r"\bpolicy context\b", r"\bdocument-level context\b", r"\bsource access\b", r"\bsource segments?\b", r"\bsource inspection\b", r"\bsource drift\b", r"\bdata source\b"]),
    ("route provenance", [r"\broute provenance\b"]),
    ("RouteMap", [r"\broutemap\b", r"\broute extraction\b", r"\broute-extraction\b", r"\broute-aware\b"]),
    ("RouteMap segment", [r"\broute segment\b", r"\bsegments?\b", r"\bpassages?\b", r"\broute passages?\b", r"\broute labels?\b", r"\broute edges?\b", r"\brelation labels?\b", r"\broute candidates?\b", r"\bdependency edge\b", r"\brole sequence\b"]),
    ("agent memory", [r"\bagent memory\b", r"\blong-context memory\b", r"\bmemory routing\b"]),
    ("long-context memory", [r"\blong-context memory\b"]),
    ("governance", [r"\bgovernance\b", r"\boversight\b", r"\baccountability\b"]),
    ("monitoring", [r"\bmonitoring\b", r"\blogging\b", r"\bincident response\b", r"\bincident reports?\b", r"\bpost-market\b"]),
    ("incident response", [r"\bincident response\b"]),
    ("documentation", [r"\bdocumentation\b"]),
    ("model behavior", [r"\bmodel behavior\b", r"\bbehaviour drift\b", r"\bbehavior drift\b"]),
    ("evaluation", [r"\bevaluation\b", r"\bevaluator\b", r"\beval\b", r"\bscore\b", r"\baccuracy\b", r"\bmetric\b", r"\bjaccard\b", r"\brecall\b", r"\bcorrectness\b"]),
    ("audit", [r"\baudit\b"]),
    ("fairness", [r"\bfairness\b", r"\bbias evidence\b"]),
]


def _clean(text: str) -> str:
    return "" if text is None else str(text).strip()


def _has_match(haystack: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, haystack) for pattern in patterns)


def _append(entities: list[str], seen: set[str], entity: str) -> None:
    key = entity.lower()
    if key not in seen:
        entities.append(entity)
        seen.add(key)


def extract_entities_v2(text: str, title: str = "") -> str:
    haystack = f"{_clean(title)} {_clean(text)}".lower()
    entities = []
    seen = set()

    for entity, patterns in ENTITY_PATTERNS:
        if _has_match(haystack, patterns):
            if entity == "data protection" and "privacy" in seen:
                _append(entities, seen, entity)
            elif entity == "model behavior":
                _append(entities, seen, entity)
            else:
                _append(entities, seen, entity)

    if "ai risk management" in seen and "ai risk" in seen:
        entities = [entity for entity in entities if entity.lower() != "ai risk"]
        seen.discard("ai risk")

    if "data" in seen and ("privacy" in seen or "data protection" in seen):
        entities = [entity for entity in entities if entity.lower() != "data"]

    if not entities:
        entities.append("RouteMap segment")

    return "; ".join(entities)
