"""Generate deterministic fresh_blind_v1 synthetic gold by construction."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter
from pathlib import Path

from validate_true_blind_gold import validate_rows


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "data/v1/fresh_blind_v1"
RAW_DOCS = OUT_ROOT / "raw_docs"
ANNOTATION_DIR = OUT_ROOT / "annotation"
REPORT_DIR = OUT_ROOT / "reports"
GOLD_PATH = ANNOTATION_DIR / "fresh_blind_gold.csv"
TEMPLATE_PATH = ANNOTATION_DIR / "fresh_blind_annotation_template.csv"
DATASET_CARD = OUT_ROOT / "DATASET_CARD.md"
TRUE_BLIND_GOLD = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"

SEED = 20260622
ROLES = ["BACKGROUND", "DEFINE", "CLAIM", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]
ROLE_SEQUENCE = ROLES + ROLES
FIELDNAMES = [
    "doc_id",
    "title",
    "segment_id",
    "source_doc",
    "source_topic",
    "segment_index",
    "route_question",
    "text",
    "segment_text",
    "role",
    "entities",
    "operative_status",
    "relation",
    "answer_relevance",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevance",
    "annotation_notes",
    "gold_answer_relevant",
    "answer_relevant",
]

DOMAINS = [
    {
        "slug": "wildfire_crew_dispatch",
        "title": "EmberDispatch Wildfire Crew Rotation",
        "question": "How should a wildfire operations desk route crew rotation decisions?",
        "entities": ["EmberDispatch", "strike team board", "fuel break map", "engine crew roster", "air tanker slot", "fatigue log"],
    },
    {
        "slug": "rail_track_possessions",
        "title": "TrackWindow Rail Possession Planning",
        "question": "How should a rail maintenance office route track possession requests?",
        "entities": ["TrackWindow", "possession calendar", "signal isolation plan", "night crew", "ballast train", "control room"],
    },
    {
        "slug": "vaccine_cold_chain",
        "title": "ColdVault Vaccine Distribution",
        "question": "How should a regional pharmacy desk route vaccine cold-chain exceptions?",
        "entities": ["ColdVault", "temperature logger", "freezer pack", "clinic tray", "courier manifest", "quarantine shelf"],
    },
    {
        "slug": "snow_route_salt",
        "title": "PlowGrid Snow Route Salting",
        "question": "How should a winter service team route salting and plowing work?",
        "entities": ["PlowGrid", "salt spreader", "priority corridor", "bridge deck sensor", "depot loader", "shift foreman"],
    },
    {
        "slug": "theater_stage_changeovers",
        "title": "StageTurn Theater Changeover Desk",
        "question": "How should a theater operations desk route stage changeover tasks?",
        "entities": ["StageTurn", "lighting plot", "fly rail cue", "prop table", "wardrobe rack", "stage manager"],
    },
    {
        "slug": "seafood_auction_grading",
        "title": "HarborScale Seafood Auction Grading",
        "question": "How should a seafood auction route grading and hold decisions?",
        "entities": ["HarborScale", "lot ticket", "ice bin", "quality grader", "buyer clock", "landing record"],
    },
    {
        "slug": "cemetery_plot_records",
        "title": "PlotLedger Cemetery Record Office",
        "question": "How should a cemetery office route plot-record corrections?",
        "entities": ["PlotLedger", "burial register", "plot map", "family deed", "marker permit", "grounds crew"],
    },
    {
        "slug": "broadband_outage_restoration",
        "title": "FiberFix Broadband Restoration",
        "question": "How should a broadband field desk route restoration work?",
        "entities": ["FiberFix", "optical node", "splice crew", "customer outage cluster", "drop cable", "network watch board"],
    },
    {
        "slug": "court_interpreter_scheduling",
        "title": "CourtVoice Interpreter Scheduling",
        "question": "How should a court coordinator route interpreter scheduling conflicts?",
        "entities": ["CourtVoice", "hearing list", "language roster", "remote booth", "case clerk", "availability hold"],
    },
    {
        "slug": "school_meal_substitutions",
        "title": "MenuSwitch School Meal Substitutions",
        "question": "How should a school nutrition office route meal substitution decisions?",
        "entities": ["MenuSwitch", "allergen note", "kitchen batch sheet", "supplier shortfall", "meal count", "cafeteria lead"],
    },
]

AVOID_TOPICS = [
    "CivicAid Permit Triage",
    "ClinicPulse Backlog Monitor",
    "EventMesh Incident Queue",
    "FraudSieve Invoice Controls",
    "GreenLedger Supplier Risk",
    "GridLens Battery Maintenance",
    "HarborFlow Container Exceptions",
    "HeritageVault Catalogue Routes",
    "LawBrief Disclosure Tracker",
    "RiverWatch Flood Notes",
    "RoboInspect Factory Checks",
    "TutorTrail Learning Routes",
]


def slugify(value):
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def read_true_blind_topics():
    if not TRUE_BLIND_GOLD.exists():
        return []
    with TRUE_BLIND_GOLD.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    topics = set()
    for row in rows:
        for key in ["title", "source_topic", "source_doc"]:
            if row.get(key):
                topics.add(row[key])
    return sorted(topics)


def json_entities(values):
    return json.dumps(values, ensure_ascii=False)


def answer_relevance(answer):
    if answer == "YES":
        return "RELEVANT"
    if answer == "NO":
        return "NOT_RELEVANT"
    return "PARTIAL"


def role_fields(role, local_index):
    if role == "BACKGROUND":
        return "DESCRIPTIVE", "sets_context", "MAYBE" if local_index % 2 else "NO"
    if role == "DEFINE":
        return "DESCRIPTIVE", "defines", "YES"
    if role == "CLAIM":
        return ("NEGATED" if local_index % 2 else "ACTIVE"), "asserts", "YES"
    if role == "METHOD":
        return "ACTIVE", ["recommends", "requires", "maps_to"][local_index % 3], "YES"
    if role == "RESULT":
        return "DESCRIPTIVE", "supports_retrieval" if local_index % 2 else "reports_usefulness", "YES"
    if role == "LIMITATION":
        return ("NEGATED" if local_index % 2 else "LIMITED"), "limits" if local_index % 2 else "warns_about", "YES"
    if role == "NEXT_STEP":
        return "ACTIVE", "proposes_next_test", "YES"
    if role == "EXAMPLE":
        return "DESCRIPTIVE", "gives_example", "YES"
    raise ValueError(role)


def segment_text(domain, role, local_index):
    e = domain["entities"]
    a, b, c, d, f, g = e
    if role == "BACKGROUND":
        variants = [
            f"{domain['title']} is a field-office packet used during ordinary handoffs, not an audit of software or policy. The packet brings together the {b}, {c}, and {d} so a supervisor can see where the next routing choice begins.",
            f"The source note comes from a local operations desk that tracks {b}, {f}, and {g} during busy shifts. It frames the work area for {a} before any recommendation is made.",
        ]
    elif role == "DEFINE":
        variants = [
            f"In this desk, the {b} means the current shared view of crews, holds, and constraints for {a}. Staff treat it as the reference object that links {c} to {d}.",
            f"The term {f} refers to the recorded item that tells the coordinator what can move, wait, or be checked again. It is narrower than the whole {a} file because it only covers the visible queue state.",
        ]
    elif role == "CLAIM":
        variants = [
            f"The routing decision is more reliable when {b} and {c} are reviewed together instead of in separate calls. That pairing keeps {d} from being treated as a side note after the main choice is already made.",
            f"The {a} desk is not sufficient when {f} is missing from the handoff, even if {b} looks complete. A coordinator still needs the missing evidence before the route can be trusted.",
        ]
    elif role == "METHOD":
        relation = ["compare", "require", "map"][local_index % 3]
        variants = [
            f"The coordinator should {relation} the {b} against the {c} before releasing the next task. If the two records disagree, the item stays with {g} until the discrepancy is cleared.",
            f"Operators first sort the {f} by urgency, then attach the matching {d} entry to each open case. The final pass sends exceptions back to the supervisor queue rather than closing them silently.",
        ]
    elif role == "RESULT":
        variants = [
            f"During the trial week, teams found that pairing {b} with {f} reduced repeated phone calls at the desk. The review also showed that {d} was the field most often used for retrieval.",
            f"A sample of completed handoffs showed that {a} made the oldest unresolved cases easier to find. Reviewers reported that {c} gave the clearest evidence when a route was challenged.",
        ]
    elif role == "LIMITATION":
        variants = [
            f"The {b} can lag behind radio updates, so it may overestimate how current the routing picture is. That caveat matters most when {g} is already working from a printed copy.",
            f"The {a} record cannot settle disputes when {c} and {f} describe different versions of the same event. Human review is still required before {d} is treated as final.",
        ]
    elif role == "NEXT_STEP":
        variants = [
            f"The next review should compare {b} entries with actual outcomes from {g}. That test would show whether {a} is routing hard cases earlier or merely documenting them later.",
            f"A follow-up sample should hold out cases where {c} arrives after the first desk decision. The team can then measure whether {f} changes the route or only confirms it.",
        ]
    elif role == "EXAMPLE":
        variants = [
            f"For example, a coordinator might receive a {f} that lists {d} as available while {c} says the work cannot start. In that case, {a} keeps the case open until {g} confirms the current state.",
            f"One routine case has {b} showing a normal queue while {d} carries a late change from the field. The desk uses that case to demonstrate why {f} is checked before closure.",
        ]
    else:
        raise ValueError(role)
    return variants[local_index % len(variants)]


def build_rows(llm_author=False):
    rng = random.Random(SEED)
    rows = []
    segment_number = 1
    for doc_number, domain in enumerate(DOMAINS, start=1):
        doc_id = f"FBV1_DOC_{doc_number:02d}_{domain['slug']}"
        roles = list(ROLE_SEQUENCE)
        rng.shuffle(roles)
        for segment_index, role in enumerate(roles, start=1):
            status, relation, answer = role_fields(role, segment_index)
            text = segment_text(domain, role, segment_index)
            if llm_author:
                text = llm_author_text(domain, role, status, relation, answer, text)
            entities = list(rng.sample(domain["entities"], k=3))
            if domain["entities"][0] not in entities:
                entities[0] = domain["entities"][0]
            row = {
                "doc_id": doc_id,
                "title": domain["title"],
                "segment_id": f"FBV1_{segment_number:04d}",
                "source_doc": doc_id,
                "source_topic": domain["title"],
                "segment_index": str(segment_index),
                "route_question": domain["question"],
                "text": text,
                "segment_text": text,
                "role": role,
                "entities": json_entities(entities),
                "operative_status": status,
                "relation": relation,
                "answer_relevance": answer_relevance(answer),
                "gold_role": role,
                "gold_entities": json_entities(entities),
                "gold_operative_status": status,
                "gold_relation": relation,
                "gold_answer_relevance": answer_relevance(answer),
                "annotation_notes": "fresh_blind_v1_gold_by_construction_seed_20260622",
                "gold_answer_relevant": answer,
                "answer_relevant": answer_relevance(answer),
            }
            rows.append(row)
            segment_number += 1
    return rows


def llm_author_text(domain, role, status, relation, answer, deterministic_text):
    import run_llm_role_classifier as role_llm

    role_llm.ensure_ollama()
    prompt = (
        "Write two natural operational-domain sentences for a synthetic benchmark row. "
        "Do not mention RouteMap, labels, roles, classifiers, AI, or benchmark construction. "
        "Preserve these exact named entities where possible: "
        f"{', '.join(domain['entities'][:4])}. Intended gold role={role}, status={status}, "
        f"relation={relation}, answer={answer}. Draft to vary: {deterministic_text}"
    )
    response = role_llm.call_ollama(prompt).strip()
    return response or deterministic_text


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in FIELDNAMES} for row in rows])


def write_template(rows):
    blank_cols = {
        "role",
        "entities",
        "operative_status",
        "relation",
        "answer_relevance",
        "gold_role",
        "gold_entities",
        "gold_operative_status",
        "gold_relation",
        "gold_answer_relevance",
        "gold_answer_relevant",
        "answer_relevant",
    }
    template_rows = []
    for row in rows:
        copied = dict(row)
        for column in blank_cols:
            copied[column] = ""
        copied["annotation_notes"] = "fresh_blind_v1_human_annotation_template"
        template_rows.append(copied)
    write_rows(TEMPLATE_PATH, template_rows)


def write_raw_docs(rows):
    RAW_DOCS.mkdir(parents=True, exist_ok=True)
    by_doc = {}
    for row in rows:
        by_doc.setdefault(row["doc_id"], []).append(row)
    for doc_id, doc_rows in by_doc.items():
        title = doc_rows[0]["title"]
        lines = [f"# {title}", "", f"Route question: {doc_rows[0]['route_question']}", ""]
        for row in doc_rows:
            lines.extend([f"## {row['segment_id']}", "", row["text"], ""])
        (RAW_DOCS / f"{doc_id}.md").write_text("\n".join(lines), encoding="utf-8")


def topic_overlap(existing_topics):
    selected = {domain["title"].lower() for domain in DOMAINS}
    existing = {topic.lower() for topic in existing_topics}
    exact = sorted(selected & existing)
    banned_terms = ["ai governance", "ai safety", "responsible ai", "llm", "route extraction"]
    banned_hits = [title for title in selected if any(term in title for term in banned_terms)]
    return exact, banned_hits


def write_dataset_card(rows, existing_topics, validation_errors):
    role_counts = Counter(row["gold_role"] for row in rows)
    exact, banned_hits = topic_overlap(existing_topics)
    lines = [
        "# fresh_blind_v1 Dataset Card",
        "",
        "fresh_blind_v1 is a deterministic synthetic blind split for an internal RouteMap sanity check.",
        "",
        "## Generation",
        "",
        f"- Seed: {SEED}",
        "- Default author: seeded templates, offline, no Ollama/provider calls.",
        "- Optional --llm-author can use local Ollama for prose only; gold remains declared by construction, but shared-model contamination risk increases.",
        "- Gold labels are assigned before prediction from declared segment intent, not inferred by the frozen model under test.",
        "",
        "## Domains",
        "",
    ]
    for domain in DOMAINS:
        lines.append(f"- {domain['title']}")
    lines.extend(
        [
            "",
            "## De-confliction",
            "",
            "Existing true-blind topics inspected and avoided:",
        ]
    )
    for topic in AVOID_TOPICS:
        lines.append(f"- {topic}")
    lines.extend(
        [
            "",
            f"Exact selected-topic overlap with existing true-blind topics: {exact or 'none'}",
            f"AI-governance/safety banned-title hits: {banned_hits or 'none'}",
            "",
            "## Balance",
            "",
        ]
    )
    for role in ROLES:
        lines.append(f"- {role}: {role_counts[role]}")
    lines.extend(
        [
            "",
            "## Caveat",
            "",
            "This is synthetic internal-sanity gold, not a publishable headline benchmark. Use fresh_blind_annotation_template.csv for independent human annotation, or replace this set with real external documents before reporting a credible external number.",
            "",
            "## Validator",
            "",
            f"Compatible true-blind schema validator errors: {validation_errors or 'none'}",
        ]
    )
    DATASET_CARD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm-author", action="store_true", help="Use local Ollama for prose only; default is deterministic offline templates.")
    args = parser.parse_args()

    rows = build_rows(llm_author=args.llm_author)
    existing_topics = read_true_blind_topics()
    exact, banned_hits = topic_overlap(existing_topics)
    if exact or banned_hits:
        raise SystemExit(f"Fresh domain de-confliction failed: exact_overlap={exact} banned_hits={banned_hits}")

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    ANNOTATION_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_raw_docs(rows)
    write_rows(GOLD_PATH, rows)
    write_template(rows)

    validation_errors, _counts = validate_rows(rows)
    write_dataset_card(rows, existing_topics, validation_errors)

    role_counts = Counter(row["gold_role"] for row in rows)
    print("fresh_blind_v1_generated")
    print("domains=" + ", ".join(domain["title"] for domain in DOMAINS))
    print(f"segment_count={len(rows)}")
    print("role_counts=" + json.dumps(dict(sorted(role_counts.items())), sort_keys=True))
    print(f"topic_overlap_exact={exact or 'none'}")
    print(f"ai_governance_overlap={banned_hits or 'none'}")
    print(f"validator_errors={validation_errors or 'none'}")
    print(f"gold={GOLD_PATH}")
    print(f"template={TEMPLATE_PATH}")
    print(f"dataset_card={DATASET_CARD}")


if __name__ == "__main__":
    main()
