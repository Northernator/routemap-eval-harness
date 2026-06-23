"""Generate de-artifacted fresh_blind_v2 synthetic gold and freeze it."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from role_taxonomies import ALLOWED_FINE_ROLES
from validate_true_blind_gold import validate_rows


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "data/v1/fresh_blind_v2"
RAW_DOCS = OUT_ROOT / "raw_docs"
ANNOTATION_DIR = OUT_ROOT / "annotation"
REPORT_DIR = OUT_ROOT / "reports"
GOLD_PATH = ANNOTATION_DIR / "fresh_blind_v2_gold.csv"
TEMPLATE_PATH = ANNOTATION_DIR / "fresh_blind_v2_annotation_template.csv"
FROZEN_GOLD = ANNOTATION_DIR / "fresh_blind_v2_gold_frozen.csv"
FREEZE_MANIFEST = REPORT_DIR / "FRESH_BLIND_V2_GOLD_FREEZE.json"
DATASET_CARD = OUT_ROOT / "DATASET_CARD.md"
TRUE_BLIND_GOLD = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
FRESH_V1_GOLD = ROOT / "data/v1/fresh_blind_v1/annotation/fresh_blind_gold_frozen.csv"

SEED = 20260623
ROLES = ["BACKGROUND", "DEFINE", "CLAIM", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]
ROLE_SEQUENCE = ROLES + ROLES
BANNED_MARKERS = [
    "means",
    "is defined",
    "defined as",
    "refers to",
    "for example",
    "for instance",
    "e.g.",
    "such as",
    "caveat",
    "however",
    "limitation",
    "next step",
    "future work",
    "we recommend",
    "result",
    "we found",
    "outcome",
    "the method",
    "the procedure",
    "background",
    "historically",
    "in summary",
]

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
        "slug": "blood_bank_platelet_allocation",
        "title": "Blood Bank Platelet Allocation",
        "question": "How should a transfusion desk route platelet allocation choices?",
        "terms": ["platelet expiry window", "crossmatch tray", "oncology ward request", "trauma cooler", "donor batch record", "night courier sheet", "blood fridge log", "compatibility hold"],
    },
    {
        "slug": "library_interlibrary_loan",
        "title": "Interlibrary Loan Queue",
        "question": "How should a library desk route borrowing and lending requests?",
        "terms": ["request slip", "lending library notice", "scanner station", "copyright page count", "patron pickup shelf", "shipping label", "journal issue record", "renewal hold"],
    },
    {
        "slug": "emergency_shelter_intake",
        "title": "Emergency Shelter Intake",
        "question": "How should a shelter desk route intake and placement decisions?",
        "terms": ["intake form", "family room list", "pet accommodation note", "transport voucher", "bed turnover sheet", "caseworker callback", "meal token drawer", "quiet room request"],
    },
    {
        "slug": "veterinary_surgery_roster",
        "title": "Veterinary Surgery Roster",
        "question": "How should a clinic route surgery scheduling conflicts?",
        "terms": ["anesthesia chart", "kennel card", "sterile pack cart", "surgeon availability board", "fasting confirmation", "recovery bay", "lab panel printout", "client consent form"],
    },
    {
        "slug": "ferry_terminal_loading",
        "title": "Ferry Terminal Loading",
        "question": "How should a terminal route vehicle loading and ramp changes?",
        "terms": ["lane marshal sheet", "vehicle height tag", "tidal clearance note", "ramp inspection card", "standby queue", "deck balance sheet", "hazmat declaration", "boarding cut-off time"],
    },
    {
        "slug": "pharmacy_compounding_queue",
        "title": "Pharmacy Compounding Queue",
        "question": "How should a pharmacy route sterile compounding work?",
        "terms": ["hood cleaning log", "batch worksheet", "dose label", "ingredient lot card", "beyond-use time", "pharmacist check tray", "delivery tote", "quarantine bin"],
    },
    {
        "slug": "fire_hydrant_inspection",
        "title": "Fire Hydrant Inspection Rounds",
        "question": "How should a field unit route hydrant inspection records?",
        "terms": ["hydrant bonnet tag", "flow pressure reading", "valve cap photo", "street repair notice", "crew tablet entry", "district map page", "paint mark", "repair ticket"],
    },
    {
        "slug": "hotel_room_turnover",
        "title": "Hotel Room Turnover Desk",
        "question": "How should a hotel desk route room turnover issues?",
        "terms": ["linen cart count", "room status board", "maintenance knock list", "guest arrival window", "minibar seal", "housekeeper assignment", "inspection note", "lost property bag"],
    },
    {
        "slug": "recycling_contamination_audit",
        "title": "Recycling Contamination Audit",
        "question": "How should a materials crew route contamination checks?",
        "terms": ["bin photo sample", "route tag", "sorting belt note", "driver observation card", "rejection sticker", "load weight ticket", "education leaflet batch", "transfer station bay"],
    },
    {
        "slug": "community_sports_fixture",
        "title": "Community Sports Fixture Desk",
        "question": "How should a league office route fixture and field conflicts?",
        "terms": ["pitch booking sheet", "referee availability grid", "club travel note", "weather closure notice", "kit clash record", "score submission form", "floodlight slot", "appeal email"],
    },
]

OLD_TOPIC_PATHS = [TRUE_BLIND_GOLD, FRESH_V1_GOLD]


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def marker_hits(text):
    lowered = text.lower()
    return [marker for marker in BANNED_MARKERS if marker in lowered]


def assert_no_markers(text):
    hits = marker_hits(text)
    if hits:
        raise ValueError(f"banned marker hit {hits}: {text}")


def json_entities(values):
    return json.dumps(values, ensure_ascii=False)


def answer_relevance(answer):
    return {"YES": "RELEVANT", "NO": "NOT_RELEVANT", "MAYBE": "PARTIAL"}[answer]


def role_fields(role, index):
    if role == "BACKGROUND":
        return "DESCRIPTIVE", "sets_context", "MAYBE" if index % 3 else "NO"
    if role == "DEFINE":
        return "DESCRIPTIVE", "defines", "YES"
    if role == "CLAIM":
        return "NEGATED" if index % 4 == 0 else "ACTIVE", "asserts", "YES"
    if role == "METHOD":
        return "ACTIVE", ["recommends", "requires", "maps_to"][index % 3], "YES"
    if role == "RESULT":
        return "DESCRIPTIVE", "supports_retrieval" if index % 2 else "reports_usefulness", "YES"
    if role == "LIMITATION":
        return "NEGATED" if index % 2 else "LIMITED", "limits" if index % 2 else "warns_about", "YES"
    if role == "NEXT_STEP":
        return "ACTIVE", "proposes_next_test", "YES"
    if role == "EXAMPLE":
        return "DESCRIPTIVE", "gives_example", "YES"
    raise ValueError(role)


def entity_pack(domain, doc_number, segment_index):
    terms = domain["terms"]
    first = terms[(segment_index - 1) % len(terms)]
    second = terms[(segment_index + 2) % len(terms)]
    local = f"{domain['slug'].replace('_', ' ')} case {doc_number}-{segment_index:02d}"
    return [first, second, local]


TEMPLATES = {
    "BACKGROUND": [
        "{a} sits beside {b} at the opening desk while {c} waits for review. Staff read the packet to understand the day before any routing choice moves.",
        "At shift handover, {a} and {b} frame the queue that includes {c}. The note gives the coordinator enough scene detail to place later entries.",
        "{c} arrives with {a} attached and {b} still unsigned. The desk keeps both items visible so the surrounding situation is clear.",
        "The office log pairs {a} with {b} because {c} often changes during the day. This record sets the working scene for the later decision.",
        "A clerk opens the folder with {a}, {b}, and {c} on the same page. The entries orient the reader before any claim about priority appears.",
        "{b} is filed next to {a} whenever {c} is active. That arrangement shows which parts of the work are already on the board.",
        "The morning sheet lists {a} and {b}, then places {c} in the pending column. The passage supplies local context rather than a directive.",
        "Before the coordinator touches the queue, {a} and {b} are checked against {c}. The detail marks the operational setting for the case.",
    ],
    "DEFINE": [
        "On this desk, {a} is the shared reference the team checks before any reassignment. It links {b} with {c} so the same object is visible to everyone.",
        "The staff use {a} as the name for the packet that joins {b} to {c}. A case lacks that item when either piece is absent.",
        "{a} is the table entry that carries {b} and {c} together. The coordinator treats the entry as one unit during handoff.",
        "Within the office, {a} is the working label for a case bundle containing {b} and {c}. It is narrower than the whole daily queue.",
        "The phrase {a} points to the record where {b} and {c} are stored together. Staff use it only for the routing object, not for the entire service.",
        "{a} names the desk artifact that joins {b} with {c}. Once the artifact is opened, both entries travel through the queue as a pair.",
        "The team calls {a} the visible case item built from {b} plus {c}. That item is what later notes attach to.",
        "For this office, {a} is the case-facing reference that holds {b} and {c}. The label stays with the file until the desk closes it.",
    ],
    "CLAIM": [
        "Pairing {a} with {b} gives the coordinator a sturdier basis for judging {c}. A case routed from only one of those records is easier to misplace.",
        "{a} carries more routing weight when {b} confirms the same case detail. Without that pairing, {c} can pull attention away from the real priority.",
        "The desk gains a clearer queue when {a} and {b} travel together. Separating them leaves {c} too much room to steer the decision.",
        "{c} should not override {a} unless {b} also supports the change. The stronger route comes from the combined case record.",
        "A coordinator can trust {a} more when {b} matches the same timeline. That pairing keeps {c} from becoming the sole signal.",
        "The safer choice comes from reading {a} beside {b}. Treating {c} alone as decisive makes the handoff weaker.",
        "{a} deserves priority only when {b} shows the same pressure. Otherwise {c} may exaggerate the urgency of the case.",
        "The queue is easier to defend when {a} anchors the file and {b} narrows it. A route based on {c} alone is less stable.",
    ],
    "METHOD": [
        "First compare {a} with {b}, then place {c} in the matching queue. If the two records disagree, hold the case for desk review.",
        "Sort {a} by time, attach {b}, and send {c} to the lane with the matching staff owner. Leave disputed entries open.",
        "Check {a}, copy the active line from {b}, and mark {c} only after the coordinator accepts the pair. The desk then releases the case.",
        "Match {a} to {b} before assigning {c}. The queue owner signs the file after the two entries line up.",
        "Read {a}, verify {b}, and route {c} through the lane already assigned to that case. Any mismatch stays in review.",
        "Group {a} with cases that share {b}, then attach {c} before closure. The clerk records who accepted the handoff.",
        "Move {a} only after {b} is present and {c} has a staff owner. The desk keeps unmatched files in the open column.",
        "Map {a} to {b}, then send {c} to the same queue. The case remains visible until the owner confirms receipt.",
    ],
    "RESULT": [
        "In the weekly review, {a} appeared in most reopened cases while {b} was usually present in clean handoffs. Reviewers used {c} to trace the difference.",
        "The trial desk saw fewer repeated calls after {a} was paired with {b}. Staff later pulled {c} when checking why the change helped.",
        "A sample of closed files showed {a} missing from several late cases. The same sample had {b} and {c} in the files that moved cleanly.",
        "Reviewers counted more timely handoffs when {a} was checked before {b}. The audit trail pointed back to {c} on the disputed cases.",
        "During the pilot, {a} matched the queue state more often than {b}. The team used {c} to confirm the pattern.",
        "The closeout review placed {a} in the files that needed fewer callbacks. {b} and {c} explained most of the remaining delays.",
        "A desk sample showed {a} reducing search time when {b} was also attached. {c} was the field most often opened during review.",
        "The month-end count showed {a} in the cases that moved before noon. Files without {b} leaned more heavily on {c}.",
    ],
    "LIMITATION": [
        "{a} can lag behind the desk conversation, so {b} may show a fresher view of {c}. The coordinator cannot close the file from that record alone.",
        "{a} is useful until {b} changes after the first review. At that point, {c} needs a second check before the route is trusted.",
        "A file can look complete when {a} is present, yet {b} may still be missing. That gap keeps {c} from being final.",
        "{a} does not settle the case when {b} points to a different queue. Staff keep {c} open until a person resolves the conflict.",
        "The desk can misread {a} when {b} arrives late. {c} stays provisional while the two records are reconciled.",
        "{a} loses value when {b} is copied from an older shift. The case tied to {c} needs review before it moves.",
        "A coordinator should treat {a} with care when {b} has no matching timestamp. {c} remains open until the file catches up.",
        "{a} cannot carry the route by itself if {b} is blank. The desk leaves {c} in review until another record confirms it.",
    ],
    "NEXT_STEP": [
        "A later sample should compare {a} with desk decisions made after {b}. The check would show whether {c} changes the queue or only documents it.",
        "The office can hold out files containing {a}, then compare them with cases built around {b}. That review would test whether {c} moves earlier.",
        "A second pass should track {a} from intake to closure and record when {b} appears. The team can then see whether {c} predicts a route change.",
        "The desk can sample twenty files where {a} and {b} disagree. Reviewers would inspect whether {c} helps choose the final lane.",
        "A later audit should separate cases with {a} from cases with only {b}. The comparison would show whether {c} adds routing value.",
        "The team can run a two-week check on {a} and record how often {b} changes the decision. {c} should be logged before and after the desk action.",
        "A follow-up table should pair {a} with the owner who handled {b}. That table would show whether {c} belongs earlier in the queue.",
        "The office should reserve a blind sample of files containing {a}. Reviewers can compare those files with {b} and score how {c} affected handoff.",
    ],
    "EXAMPLE": [
        "One file has {a} arriving before {b}, while {c} remains unsigned. The coordinator keeps the case open until the two desk records match.",
        "A routine case shows {a} on the morning list and {b} in the afternoon packet. {c} then explains why the owner changed the lane.",
        "A clerk might see {a} already attached but {b} still waiting in the tray. The case tied to {c} stays out of the closed column.",
        "One Tuesday file carries {a}, {b}, and a late note about {c}. The desk uses that mix to show how a small mismatch changes routing.",
        "A sample handoff begins with {a} in place and {b} missing from the packet. {c} gives the reviewer the reason for keeping the file open.",
        "A caller asks about {a} while the desk is still waiting for {b}. The coordinator checks {c} before assigning the next owner.",
        "One closed case includes {a} and {b}, but the desk later reopens it after reading {c}. The file shows how a small detail changes the lane.",
        "A late-day entry has {a} in the queue and {b} on a separate sheet. The coordinator links both to {c} before moving the case.",
    ],
}


def read_topics(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    topics = set()
    for row in rows:
        for key in ["title", "source_topic", "source_doc"]:
            if row.get(key):
                topics.add(row[key])
    return sorted(topics)


def topic_overlap(old_topics):
    selected = {domain["title"].lower() for domain in DOMAINS}
    exact = sorted(selected & {topic.lower() for topic in old_topics})
    banned_terms = ["ai governance", "ai safety", "responsible ai", "llm", "route extraction"]
    banned_hits = sorted(title for title in selected if any(term in title for term in banned_terms))
    return exact, banned_hits


def row_text(role, entities, template_index):
    template = TEMPLATES[role][template_index % len(TEMPLATES[role])]
    return template.format(a=entities[0], b=entities[1], c=entities[2])


def build_rows():
    rng = random.Random(SEED)
    rows = []
    segment_number = 1
    role_openers = defaultdict(Counter)
    for doc_number, domain in enumerate(DOMAINS, start=1):
        doc_id = f"FBV2_DOC_{doc_number:02d}_{domain['slug']}"
        roles = list(ROLE_SEQUENCE)
        rng.shuffle(roles)
        for segment_index, role in enumerate(roles, start=1):
            status, relation, answer = role_fields(role, segment_index)
            entities = entity_pack(domain, doc_number, segment_index)
            template_index = (segment_index + doc_number * 3 + ROLES.index(role)) % len(TEMPLATES[role])
            text = row_text(role, entities, template_index)
            assert_no_markers(text)
            opener = " ".join(text.split()[:3]).lower()
            if role_openers[role][opener] >= 2:
                template_index = (template_index + 3) % len(TEMPLATES[role])
                text = row_text(role, entities, template_index)
                assert_no_markers(text)
                opener = " ".join(text.split()[:3]).lower()
            role_openers[role][opener] += 1
            row = {
                "doc_id": doc_id,
                "title": domain["title"],
                "segment_id": f"FBV2_{segment_number:04d}",
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
                "annotation_notes": "fresh_blind_v2_gold_by_construction_seed_20260623",
                "gold_answer_relevant": answer,
                "answer_relevant": answer_relevance(answer),
            }
            rows.append(row)
            segment_number += 1
    return rows


def parse_entities(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        parsed = json.loads(text)
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [part.strip() for part in text.split(";") if part.strip()]


def validation_metrics(rows):
    total_entities = 0
    verbatim = 0
    unique_entities = set()
    marker_counts = Counter()
    role_counts = Counter()
    for row in rows:
        text = row["segment_text"].lower()
        role = row["gold_role"]
        role_counts[role] += 1
        marker_counts[role] += int(bool(marker_hits(row["segment_text"])))
        for entity in parse_entities(row["gold_entities"]):
            total_entities += 1
            unique_entities.add(entity.lower())
            verbatim += int(entity.lower() in text)
    banned_by_role = {
        role: marker_counts[role] / role_counts[role] if role_counts[role] else 0.0
        for role in ROLES
    }
    return {
        "verbatim_entity_rate": verbatim / total_entities if total_entities else 0.0,
        "banned_marker_hit_rate_by_role": banned_by_role,
        "banned_marker_hit_rate": sum(marker_counts.values()) / len(rows) if rows else 0.0,
        "entity_vocab_diversity": len(unique_entities) / total_entities if total_entities else 0.0,
        "unique_entities": len(unique_entities),
        "total_entity_mentions": total_entities,
    }


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "can", "for", "from", "has",
    "have", "if", "in", "into", "is", "it", "its", "more", "not", "of", "on", "or", "so",
    "than", "that", "the", "their", "then", "this", "to", "under", "when", "where", "while",
    "with", "without",
}


def tokens(text):
    words = [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOPWORDS and len(word) > 1]
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]


def nb_train(rows):
    class_counts = Counter()
    feature_counts = {role: Counter() for role in ROLES}
    feature_totals = Counter()
    vocab = set()
    for row in rows:
        role = row["gold_role"]
        class_counts[role] += 1
        for feature in tokens(row["segment_text"]):
            feature_counts[role][feature] += 1
            feature_totals[role] += 1
            vocab.add(feature)
    return class_counts, feature_counts, feature_totals, vocab


def nb_predict(model, text):
    class_counts, feature_counts, feature_totals, vocab = model
    class_total = sum(class_counts.values())
    vocab_size = max(1, len(vocab))
    feats = tokens(text)
    scores = {}
    for role in ROLES:
        score = math.log((class_counts[role] + 1) / (class_total + len(ROLES)))
        denom = feature_totals[role] + vocab_size
        for feature in feats:
            score += math.log((feature_counts[role].get(feature, 0) + 1) / denom)
        scores[role] = score
    return max(scores.items(), key=lambda item: (item[1], item[0]))[0]


def telegraph_probe_accuracy(rows, folds=5):
    correct = 0
    total = 0
    ordered = sorted(rows, key=lambda row: row["segment_id"])
    for fold in range(folds):
        train = [row for index, row in enumerate(ordered) if index % folds != fold]
        test = [row for index, row in enumerate(ordered) if index % folds == fold]
        model = nb_train(train)
        for row in test:
            correct += int(nb_predict(model, row["segment_text"]) == row["gold_role"])
            total += 1
    return correct / total if total else 0.0


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in FIELDNAMES} for row in rows])


def write_template(rows):
    blank_cols = {
        "role", "entities", "operative_status", "relation", "answer_relevance", "gold_role",
        "gold_entities", "gold_operative_status", "gold_relation", "gold_answer_relevance",
        "gold_answer_relevant", "answer_relevant",
    }
    template = []
    for row in rows:
        copied = dict(row)
        for column in blank_cols:
            copied[column] = ""
        copied["annotation_notes"] = "fresh_blind_v2_human_annotation_template"
        template.append(copied)
    write_rows(TEMPLATE_PATH, template)


def write_raw_docs(rows):
    RAW_DOCS.mkdir(parents=True, exist_ok=True)
    by_doc = defaultdict(list)
    for row in rows:
        by_doc[row["doc_id"]].append(row)
    for doc_id, doc_rows in by_doc.items():
        lines = [f"# {doc_rows[0]['title']}", "", f"Route question: {doc_rows[0]['route_question']}", ""]
        for row in doc_rows:
            lines.extend([f"## {row['segment_id']}", "", row["segment_text"], ""])
        (RAW_DOCS / f"{doc_id}.md").write_text("\n".join(lines), encoding="utf-8")


def freeze_gold(rows, metrics, telegraph_probe):
    current_hash = file_sha256(GOLD_PATH)
    manifest = {
        "dataset": "fresh_blind_v2",
        "gold_path": str(GOLD_PATH.relative_to(ROOT)),
        "frozen_gold_path": str(FROZEN_GOLD.relative_to(ROOT)),
        "sha256": current_hash,
        "row_count": len(rows),
        "role_counts": dict(sorted(Counter(row["gold_role"] for row in rows).items())),
        "validation_metrics": metrics,
        "telegraph_probe_8role_accuracy": telegraph_probe,
        "rule": "Freeze before prediction. If fresh_blind_v2_gold.csv hash changes after this manifest exists, evaluation refuses to run.",
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if FREEZE_MANIFEST.exists():
        previous = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
        if previous.get("sha256") != current_hash:
            raise SystemExit(f"Refusing to overwrite existing freeze manifest with changed hash: {FREEZE_MANIFEST}")
        if not FROZEN_GOLD.exists():
            shutil.copyfile(GOLD_PATH, FROZEN_GOLD)
        return previous
    shutil.copyfile(GOLD_PATH, FROZEN_GOLD)
    FREEZE_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def write_dataset_card(rows, old_topics, metrics, telegraph_probe):
    role_counts = Counter(row["gold_role"] for row in rows)
    exact, banned = topic_overlap(old_topics)
    lines = [
        "# fresh_blind_v2 Dataset Card",
        "",
        "fresh_blind_v2 is a deterministic synthetic blind split with de-artifacting checks.",
        "",
        "## Generation",
        "",
        f"- Seed: {SEED}",
        "- Offline templates only; no Ollama/provider calls.",
        "- Gold is assigned by construction from segment intent before prediction.",
        "- Banned lexical markers are rejected during generation.",
        "- Gold entities are segment-local noun phrases and must appear verbatim in their segment.",
        "",
        "## Domains",
        "",
    ]
    for domain in DOMAINS:
        lines.append(f"- {domain['title']}")
    lines.extend(["", "## De-confliction", "", f"- Exact overlap with old topics: {exact or 'none'}", f"- AI-governance/safety title hits: {banned or 'none'}", ""])
    lines.extend(["## Balance", ""])
    for role in ROLES:
        lines.append(f"- {role}: {role_counts[role]}")
    lines.extend(
        [
            "",
            "## Validation Gate",
            "",
            f"- verbatim_entity_rate: {metrics['verbatim_entity_rate']:.6f}",
            f"- banned_marker_hit_rate: {metrics['banned_marker_hit_rate']:.6f}",
            f"- entity_vocab_diversity: {metrics['entity_vocab_diversity']:.6f}",
            f"- telegraph_probe_8role_accuracy: {telegraph_probe:.6f}",
            "",
            "## Caveat",
            "",
            "This remains synthetic gold. Use the annotation template for independent human annotation, or build a real external-document blind split before publishing a credible headline.",
        ]
    )
    DATASET_CARD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = build_rows()
    old_topics = []
    for path in OLD_TOPIC_PATHS:
        old_topics.extend(read_topics(path))
    exact_overlap, ai_hits = topic_overlap(old_topics)
    if exact_overlap or ai_hits:
        raise SystemExit(f"Topic de-confliction failed: exact_overlap={exact_overlap} ai_hits={ai_hits}")

    metrics = validation_metrics(rows)
    telegraph_probe = telegraph_probe_accuracy(rows)
    if metrics["verbatim_entity_rate"] < 0.97:
        raise SystemExit(f"verbatim_entity_rate below target: {metrics['verbatim_entity_rate']:.6f}")
    if metrics["banned_marker_hit_rate"] > 0:
        raise SystemExit(f"banned_marker_hit_rate not zero: {metrics['banned_marker_hit_rate']:.6f}")

    errors, _counts = validate_rows(rows)
    if errors:
        raise SystemExit("fresh_blind_v2 schema validation failed:\n" + "\n".join(errors))

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    ANNOTATION_DIR.mkdir(parents=True, exist_ok=True)
    write_raw_docs(rows)
    write_rows(GOLD_PATH, rows)
    write_template(rows)
    manifest = freeze_gold(rows, metrics, telegraph_probe)
    write_dataset_card(rows, old_topics, metrics, telegraph_probe)

    role_counts = Counter(row["gold_role"] for row in rows)
    print("fresh_blind_v2_generated")
    print("domains=" + ", ".join(domain["title"] for domain in DOMAINS))
    print(f"segment_count={len(rows)}")
    print("role_counts=" + json.dumps(dict(sorted(role_counts.items())), sort_keys=True))
    print(f"topic_overlap_exact={exact_overlap or 'none'}")
    print(f"ai_governance_overlap={ai_hits or 'none'}")
    print(f"verbatim_entity_rate={metrics['verbatim_entity_rate']:.6f}")
    print(f"banned_marker_hit_rate={metrics['banned_marker_hit_rate']:.6f}")
    print("banned_marker_hit_rate_by_role=" + json.dumps(metrics["banned_marker_hit_rate_by_role"], sort_keys=True))
    print(f"entity_vocab_diversity={metrics['entity_vocab_diversity']:.6f}")
    print(f"telegraph_probe_8role_accuracy={telegraph_probe:.6f}")
    if telegraph_probe >= 0.55:
        print("WARNING: telegraph probe >= 0.55; residual surface leakage likely remains.")
    print(f"gold_sha256={manifest['sha256']}")
    print(f"gold={GOLD_PATH}")
    print(f"frozen_gold={FROZEN_GOLD}")
    print(f"freeze_manifest={FREEZE_MANIFEST}")
    print(f"dataset_card={DATASET_CARD}")


if __name__ == "__main__":
    main()
