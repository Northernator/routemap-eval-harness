import csv
from pathlib import Path


OUT_PATH = Path("data/v1/gold/expanded_boundary_entity_dataset_v2.csv")
ROLES = ["BACKGROUND", "CLAIM", "DEFINE", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]
BOUNDARY_PAIRS = [
    ("CLAIM", "DEFINE"),
    ("RESULT", "CLAIM"),
    ("BACKGROUND", "CLAIM"),
    ("BACKGROUND", "EXAMPLE"),
    ("BACKGROUND", "RESULT"),
    ("METHOD", "EXAMPLE"),
    ("RESULT", "METHOD"),
    ("CLAIM", "METHOD"),
]
ENTITIES = [
    "AI safety evaluation",
    "model release governance",
    "privacy",
    "consent boundary",
    "permission boundary",
    "retrieval trace",
    "route provenance",
    "RouteMap",
    "route extraction",
    "benchmark",
    "evaluation",
    "human review",
    "evidence selection",
    "tool-use security",
    "incident response",
    "agent memory",
    "audit trail",
    "answer support",
    "policy context",
    "controls",
    "risk management",
    "source context",
    "mismatch review",
    "gold labels",
    "RouteMap segment",
    "secure AI development",
    "LLM application security",
]
FIELDNAMES = [
    "segment_id",
    "dataset_family",
    "boundary_pair",
    "title",
    "text",
    "gold_role",
    "contrast_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "difficulty",
    "notes",
]


def relation_for(role):
    return {
        "BACKGROUND": "sets_context",
        "DEFINE": "defines",
        "CLAIM": "asserts",
        "METHOD": "recommends",
        "RESULT": "reports_usefulness",
        "LIMITATION": "limits",
        "NEXT_STEP": "proposes_next_test",
        "EXAMPLE": "gives_example",
    }[role]


def status_for(role):
    return {
        "BACKGROUND": "DESCRIPTIVE",
        "DEFINE": "DESCRIPTIVE",
        "CLAIM": "ACTIVE",
        "METHOD": "ACTIVE",
        "RESULT": "DESCRIPTIVE",
        "LIMITATION": "LIMITED",
        "NEXT_STEP": "ACTIVE",
        "EXAMPLE": "DESCRIPTIVE",
    }[role]


def relevance_for(role):
    return "MAYBE" if role == "BACKGROUND" else "YES"


def pick_entities(index, role):
    base = [ENTITIES[index % len(ENTITIES)], ENTITIES[(index * 3 + 5) % len(ENTITIES)]]
    if role in {"RESULT", "METHOD"}:
        base.append("evaluation" if role == "RESULT" else "controls")
    if role in {"BACKGROUND", "CLAIM"}:
        base.append("source context" if role == "BACKGROUND" else "risk management")
    return list(dict.fromkeys(base))[:4]


def sentence(role, contrast, idx, entities):
    e1 = entities[0]
    e2 = entities[1] if len(entities) > 1 else "RouteMap"
    variants = {
        "BACKGROUND": [
            f"A source packet frames {e1} alongside {e2} so reviewers can place the passage before judging its route label.",
            f"The project note records why {e1} and {e2} appear together in the benchmark context.",
            f"A policy context page introduces {e1} vocabulary before any substantive extraction claim is made.",
        ],
        "CLAIM": [
            f"{e1} improves RouteMap reliability only when {e2} remains visible to downstream reviewers.",
            f"A route-aware system loses answer support when {e1} is separated from {e2}.",
            f"{e1} should be treated as evidence for route quality rather than as decorative metadata.",
        ],
        "DEFINE": [
            f"{e1} names the boundary where {e2} becomes part of the route record.",
            f"In this benchmark, {e1} denotes the label used for passages that carry {e2}.",
            f"The phrase {e1} marks the identity of the route feature connected to {e2}.",
        ],
        "METHOD": [
            f"The reviewer logs {e1}, checks {e2}, and stores the route decision before publishing the answer.",
            f"The workflow compares {e1} against {e2} and records the selected evidence in the audit trail.",
            f"RouteMap processing links {e1} to {e2}, validates the label, and preserves the reviewer note.",
        ],
        "RESULT": [
            f"The evaluation run recovered {e1} but missed {e2} in several hard boundary rows.",
            f"The mismatch review shows {e1} improved after adding labels while {e2} remained unstable.",
            f"The benchmark output reports that {e1} was selected more consistently than {e2}.",
        ],
        "LIMITATION": [
            f"{e1} alone is insufficient when {e2} is absent from the retrieved passage.",
            f"The route remains ambiguous unless {e1} and {e2} are both visible to human review.",
            f"Without {e1}, the extractor may overstate {e2} and hide a residual route gap.",
        ],
        "NEXT_STEP": [
            f"The next benchmark should compare {e1} with {e2} on unseen route-retrieval documents.",
            f"A follow-up evaluation should add harder examples where {e1} nearly overlaps with {e2}.",
            f"Future corpora should include paired rows that separate {e1} from {e2}.",
        ],
        "EXAMPLE": [
            f"In one release review, a reviewer accepted {e1} but sent {e2} back for a second check.",
            f"A tenant report shows {e1} in the retrieved path while {e2} appears only in the notes.",
            f"During an incident drill, the audit trail links {e1} to one passage and {e2} to another.",
        ],
    }
    return variants[role][idx % 3]


def make_row(segment, family, pair, title, text, role, contrast, entities, difficulty, notes):
    return {
        "segment_id": f"EXPAND_S{segment:04d}",
        "dataset_family": family,
        "boundary_pair": pair,
        "title": title,
        "text": text,
        "gold_role": role,
        "contrast_role": contrast,
        "gold_entities": "; ".join(entities),
        "gold_operative_status": status_for(role),
        "gold_relation": relation_for(role),
        "gold_answer_relevant": relevance_for(role),
        "difficulty": difficulty,
        "notes": notes,
    }


def main():
    rows = []
    segment = 1
    difficulties = ["MEDIUM", "HARD", "MEDIUM", "EASY", "HARD"]
    for left, right in BOUNDARY_PAIRS:
        pair = f"{left} vs {right}"
        for i in range(50):
            role = left if i < 25 else right
            contrast = right if role == left else left
            entities = pick_entities(segment, role)
            rows.append(make_row(
                segment,
                "boundary_pair",
                pair,
                f"expanded_boundary_{segment:04d}.md",
                sentence(role, contrast, segment, entities),
                role,
                contrast,
                entities,
                difficulties[(i + segment) % len(difficulties)],
                f"Intended as {role} rather than {contrast} for the {pair} boundary.",
            ))
            segment += 1

    for i in range(160):
        role = ROLES[i % len(ROLES)]
        main_entity = ENTITIES[i % len(ENTITIES)]
        extra = ENTITIES[(i + 9) % len(ENTITIES)]
        near = ENTITIES[(i + 17) % len(ENTITIES)]
        entities = list(dict.fromkeys([main_entity, extra, "RouteMap" if i % 4 == 0 else near]))[:4]
        text = sentence(role, "ENTITY_NEAR_MISS", i, entities)
        if i % 5 == 0:
            text += f" The nearby phrase mentions {near.lower()} only as a contrast, not the main label."
        rows.append(make_row(
            segment,
            "entity_focus",
            "ENTITY_COVERAGE",
            f"expanded_entity_{segment:04d}.md",
            text,
            role,
            "ENTITY_NEAR_MISS",
            entities,
            difficulties[(i + 2) % len(difficulties)],
            f"Entity coverage row for {main_entity} with controlled near miss.",
        ))
        segment += 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Rows written: {len(rows)}")
    print(f"Output: {OUT_PATH}")


if __name__ == "__main__":
    main()
