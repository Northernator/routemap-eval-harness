import csv
import shutil
from collections import Counter
from pathlib import Path

from validate_true_blind_gold import GOLD, VALID_ANSWERS, VALID_RELATIONS, VALID_ROLES, VALID_STATUS


ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold.pre_label_patch_backup.csv"

ROLE_ALIASES = {
    "MODIFY": "METHOD",
    "EXCEPT": "LIMITATION",
}

STATUS_ALIASES = {
    "OPERATIVE": "ACTIVE",
    "NON_OPERATIVE": "DESCRIPTIVE",
}

RELATION_ALIASES = {
    "SUPPORTS": "supports_retrieval",
    "CONTEXT": "sets_context",
    "CONSTRAINS": "limits",
    "RESULT_OF": "reports_usefulness",
    "NEXT_STEP": "proposes_next_test",
    "EXEMPLIFIES": "gives_example",
    "MODIFIES": "maps_to",
    "EXCEPTS": "limits",
}

ANSWER_ALIASES = {
    "RELEVANT": "YES",
}


def clean(value):
    return "" if value is None else str(value).strip()


def normalize(value, aliases):
    value = clean(value)
    return aliases.get(value, value)


def read_rows():
    if not GOLD.exists():
        raise FileNotFoundError(f"Missing true-blind gold file: {GOLD}")
    with GOLD.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    if not rows:
        raise ValueError(f"No rows found in {GOLD}")
    return fieldnames, rows


def ensure_backup():
    if BACKUP.exists():
        return "reused_existing_backup"
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GOLD, BACKUP)
    return "created_backup"


def patch_rows(rows):
    counts = Counter()
    for row in rows:
        original = {
            "gold_role": clean(row.get("gold_role")),
            "gold_operative_status": clean(row.get("gold_operative_status")),
            "gold_relation": clean(row.get("gold_relation")),
            "gold_answer_relevant": clean(row.get("gold_answer_relevant")),
        }
        patched = {
            "gold_role": normalize(original["gold_role"], ROLE_ALIASES),
            "gold_operative_status": normalize(original["gold_operative_status"], STATUS_ALIASES),
            "gold_relation": normalize(original["gold_relation"], RELATION_ALIASES),
            "gold_answer_relevant": normalize(original["gold_answer_relevant"], ANSWER_ALIASES),
        }
        for column, before in original.items():
            after = patched[column]
            if before != after:
                counts[f"{column}:{before}->{after}"] += 1
            row[column] = after
    return counts


def validate_patched(rows):
    errors = []
    for row_number, row in enumerate(rows, start=2):
        segment_id = clean(row.get("segment_id")) or "(blank)"
        role = clean(row.get("gold_role"))
        status = clean(row.get("gold_operative_status"))
        relation = clean(row.get("gold_relation"))
        answer = clean(row.get("gold_answer_relevant"))
        if role not in VALID_ROLES:
            errors.append(f"row {row_number} segment {segment_id}: invalid gold_role {role!r}")
        if status not in VALID_STATUS:
            errors.append(f"row {row_number} segment {segment_id}: invalid gold_operative_status {status!r}")
        if relation not in VALID_RELATIONS:
            errors.append(f"row {row_number} segment {segment_id}: invalid gold_relation {relation!r}")
        if answer not in VALID_ANSWERS:
            errors.append(f"row {row_number} segment {segment_id}: invalid gold_answer_relevant {answer!r}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)


def write_rows(fieldnames, rows):
    with GOLD.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_allowed():
    print("allowed_gold_role=" + ",".join(sorted(VALID_ROLES)))
    print("allowed_gold_operative_status=" + ",".join(sorted(VALID_STATUS)))
    print("allowed_gold_relation=" + ",".join(sorted(VALID_RELATIONS)))
    print("allowed_gold_answer_relevant=" + ",".join(sorted(VALID_ANSWERS)))


def main():
    fieldnames, rows = read_rows()
    print_allowed()
    backup_status = ensure_backup()
    counts = patch_rows(rows)
    validate_patched(rows)
    write_rows(fieldnames, rows)
    print(f"backup_status={backup_status}")
    print(f"backup_path={BACKUP.relative_to(ROOT)}")
    print(f"patched_gold_path={GOLD.relative_to(ROOT)}")
    print(f"row_count={len(rows)}")
    print("mapping_counts")
    for key, count in sorted(counts.items()):
        print(f"- {key}: {count}")
    print("patch_result=PASS")


if __name__ == "__main__":
    main()
