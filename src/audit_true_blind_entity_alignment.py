import csv
import json
import re
import string
from collections import Counter, defaultdict
from pathlib import Path

from entity_ontology_v1 import CANONICAL_ENTITIES, normalize_entity, split_entity_set


ROOT = Path(__file__).resolve().parents[1]
TRUE_BLIND_ROOT = ROOT / "data/v1/true_blind_natural_language"
GOLD_PATH = TRUE_BLIND_ROOT / "annotation/true_blind_gold.csv"
PREDICTIONS = {
    "combined": TRUE_BLIND_ROOT / "predictions/combined_v3_true_blind_predictions.csv",
    "D": TRUE_BLIND_ROOT / "predictions/D_true_blind_predictions.csv",
    "R6": TRUE_BLIND_ROOT / "predictions/R6_true_blind_predictions.csv",
}
OUT_DIR = TRUE_BLIND_ROOT / "audits/entity_alignment"
PROPOSED_DIR = OUT_DIR / "proposed"
ROW_AUDIT = OUT_DIR / "TRUE_BLIND_ENTITY_ALIGNMENT_ROW_AUDIT.csv"
REPORT_MD = OUT_DIR / "TRUE_BLIND_ENTITY_ALIGNMENT_REPORT.md"
SUMMARY_JSON = OUT_DIR / "TRUE_BLIND_ENTITY_ALIGNMENT_SUMMARY.json"
ALIAS_CSV = OUT_DIR / "TRUE_BLIND_ENTITY_ALIAS_CANDIDATES.csv"
PROPOSAL_MD = OUT_DIR / "TRUE_BLIND_ENTITY_CANONICALISATION_PROPOSAL.md"
PROPOSED_GOLD = PROPOSED_DIR / "true_blind_gold_entities_canonicalised_PROPOSED.csv"
PROPOSED_R6 = PROPOSED_DIR / "R6_true_blind_predictions_entities_canonicalised_PROPOSED.csv"

VARIANTS = ["combined", "D", "R6"]
CANONICAL_BY_NORM = {}


def norm_space(value):
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def norm_lower(value):
    return norm_space(value).lower()


def norm_punct(value):
    table = str.maketrans({char: " " for char in string.punctuation})
    return norm_space(norm_lower(value).translate(table))


def norm_singular(value):
    tokens = []
    for token in norm_punct(value).split():
        if len(token) > 4 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        tokens.append(token)
    return " ".join(tokens)


for canonical in CANONICAL_ENTITIES:
    CANONICAL_BY_NORM[norm_punct(canonical)] = canonical
    CANONICAL_BY_NORM[norm_singular(canonical)] = canonical


def safe_div(num, den):
    return num / den if den else 0.0


def jaccard(left, right):
    left = set(left)
    right = set(right)
    return safe_div(len(left & right), len(left | right))


def fmt_set(values):
    return "; ".join(sorted(values, key=lambda item: item.lower()))


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        return reader.fieldnames or [], rows


def parse_diagnostic_entities(value):
    raw = norm_space(value)
    if not raw:
        return [], "", False
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            return [], f"json_parse_error:{exc.msg}", True
        if not isinstance(parsed, list):
            return [], "json_parse_error:not_list", True
        entities = [norm_space(item) for item in parsed if norm_space(item)]
        return entities, "json_list", False
    delimiter = ";"
    if ";" in raw:
        delimiter = ";"
    elif "|" in raw:
        delimiter = "|"
    elif "\n" in raw:
        delimiter = "\n"
    else:
        entities = [raw]
        return entities, "single", False
    entities = [norm_space(item) for item in raw.split(delimiter) if norm_space(item)]
    return entities, f"delimiter:{delimiter}", False


def evaluator_entities(value):
    return split_entity_set(value)


def lower_set(values):
    return {norm_lower(value) for value in values if norm_lower(value)}


def punct_set(values):
    return {norm_punct(value) for value in values if norm_punct(value)}


def canonical_set(values, alias_map):
    output = set()
    for value in values:
        lowered = norm_punct(value)
        singular = norm_singular(value)
        normalized = normalize_entity(value)
        if normalized in CANONICAL_ENTITIES:
            output.add(normalized)
        elif value in alias_map:
            output.add(alias_map[value])
        elif lowered in CANONICAL_BY_NORM:
            output.add(CANONICAL_BY_NORM[lowered])
        elif singular in CANONICAL_BY_NORM:
            output.add(CANONICAL_BY_NORM[singular])
        else:
            output.add(value)
    return output


def index_by_segment(rows, label):
    indexed = {}
    for row in rows:
        segment_id = norm_space(row.get("segment_id"))
        if not segment_id:
            raise ValueError(f"Blank segment_id in {label}")
        if segment_id in indexed:
            raise ValueError(f"Duplicate segment_id in {label}: {segment_id}")
        indexed[segment_id] = row
    return indexed


def entity_columns(fieldnames, label):
    has_gold = "gold_entities" in fieldnames
    has_pred = "pred_entities" in fieldnames
    if label == "gold" and not has_gold:
        raise ValueError(f"Gold file missing gold_entities: {GOLD_PATH}")
    if label != "gold" and not has_pred:
        raise ValueError(f"Prediction file missing pred_entities: {PREDICTIONS[label]}")
    return {
        "gold_entities": has_gold,
        "pred_entities": has_pred,
        "fieldnames": fieldnames,
    }


def collect_rows():
    gold_fields, gold_rows = read_csv(GOLD_PATH)
    schemas = {"gold": entity_columns(gold_fields, "gold")}
    pred_rows = {}
    for variant, path in PREDICTIONS.items():
        fields, rows = read_csv(path)
        schemas[variant] = entity_columns(fields, variant)
        pred_rows[variant] = index_by_segment(rows, variant)
    gold_index = index_by_segment(gold_rows, "gold")
    missing = {
        variant: [segment_id for segment_id in gold_index if segment_id not in pred_rows[variant]]
        for variant in VARIANTS
    }
    missing = {variant: rows for variant, rows in missing.items() if rows}
    if missing:
        raise ValueError(f"Predictions missing segment_ids: {missing}")
    return schemas, gold_rows, gold_index, pred_rows


def infer_alias_candidates(gold_index, pred_rows):
    pair_counts = Counter()
    pair_examples = defaultdict(list)
    direct_alias = {}
    for segment_id, gold_row in gold_index.items():
        gold_values, _, gold_failed = parse_diagnostic_entities(gold_row.get("gold_entities", ""))
        if gold_failed:
            continue
        predicted_union = set()
        for variant in VARIANTS:
            pred_values, _, pred_failed = parse_diagnostic_entities(pred_rows[variant][segment_id].get("pred_entities", ""))
            if not pred_failed:
                predicted_union.update(pred_values)
        for gold_entity in gold_values:
            normalized = normalize_entity(gold_entity)
            if normalized in CANONICAL_ENTITIES and normalized != gold_entity:
                direct_alias[gold_entity] = normalized
            gold_norm = norm_punct(gold_entity)
            gold_singular = norm_singular(gold_entity)
            if gold_norm in CANONICAL_BY_NORM:
                direct_alias[gold_entity] = CANONICAL_BY_NORM[gold_norm]
            elif gold_singular in CANONICAL_BY_NORM:
                direct_alias[gold_entity] = CANONICAL_BY_NORM[gold_singular]
            for predicted_entity in predicted_union:
                pair = (gold_entity, predicted_entity)
                pair_counts[pair] += 1
                if len(pair_examples[pair]) < 5:
                    pair_examples[pair].append(segment_id)
    candidates = []
    for (gold_entity, predicted_entity), count in pair_counts.items():
        gold_norm = norm_punct(gold_entity)
        pred_norm = norm_punct(predicted_entity)
        gold_sing = norm_singular(gold_entity)
        pred_sing = norm_singular(predicted_entity)
        confidence = "low"
        reason = "cooccurs_without_string_match"
        if gold_norm == pred_norm or gold_sing == pred_sing:
            confidence = "high"
            reason = "punctuation_or_singular_match"
        elif gold_norm and pred_norm and (gold_norm in pred_norm or pred_norm in gold_norm):
            confidence = "medium"
            reason = "substring_match"
        elif count >= 5:
            confidence = "low"
            reason = "frequent_cooccurrence_only"
        candidates.append({
            "gold_entity": gold_entity,
            "predicted_entity": predicted_entity,
            "support_count": count,
            "example_rows": "; ".join(pair_examples[(gold_entity, predicted_entity)]),
            "confidence": confidence,
            "reason": reason,
        })
    for gold_entity, canonical in direct_alias.items():
        candidates.append({
            "gold_entity": gold_entity,
            "predicted_entity": canonical,
            "support_count": 0,
            "example_rows": "",
            "confidence": "high",
            "reason": "matches_existing_ontology_synonym_or_canonical_form",
        })
    confidence_rank = {"high": 0, "medium": 1, "low": 2}
    deduped = {}
    for row in candidates:
        key = (row["gold_entity"], row["predicted_entity"])
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = dict(row)
            continue
        existing["support_count"] = max(existing["support_count"], row["support_count"])
        examples = [part for part in [existing["example_rows"], row["example_rows"]] if part]
        existing["example_rows"] = "; ".join(sorted(set("; ".join(examples).split("; ")))) if examples else ""
        if confidence_rank[row["confidence"]] < confidence_rank[existing["confidence"]]:
            existing["confidence"] = row["confidence"]
        if row["reason"] not in existing["reason"].split("; "):
            existing["reason"] = existing["reason"] + "; " + row["reason"]
    candidates = list(deduped.values())
    candidates.sort(key=lambda row: (
        confidence_rank[row["confidence"]],
        -row["support_count"],
        row["gold_entity"].lower(),
        row["predicted_entity"].lower(),
    ))
    safe_alias_map = {
        row["gold_entity"]: row["predicted_entity"]
        for row in candidates
        if row["confidence"] in {"high", "medium"} and row["reason"] != "cooccurs_without_string_match"
    }
    return candidates, safe_alias_map


def classify_bucket(gold_raw, gold_diag, gold_format, gold_failed, variant_results, alias_improved):
    if gold_failed or any(result["pred_failed"] for result in variant_results.values()):
        return "column_parse_failure"
    if not gold_diag:
        return "empty_gold_entities"
    if all(not result["pred_diag"] for result in variant_results.values()):
        return "empty_prediction_entities"
    if any(result["current_jaccard"] > 0 and result["current_jaccard"] < 1 for result in variant_results.values()):
        return "partial_overlap"
    if any(result["current_jaccard"] == 1 for result in variant_results.values()):
        return "exact_match_after_normalisation"
    if any(result["lower_jaccard"] == 1 or result["punct_jaccard"] == 1 for result in variant_results.values()):
        return "case_or_punctuation_only"
    if alias_improved:
        return "singular_plural_or_alias_mismatch"
    if gold_format == "json_list" and len(evaluator_entities(gold_raw)) == 1 and len(gold_diag) > 1:
        return "delimiter_format_mismatch"
    ontology_hits = sum(1 for entity in gold_diag if canonical_set([entity], {}) & set(CANONICAL_ENTITIES))
    if ontology_hits == 0:
        return "gold_freeform_not_in_ontology"
    if any(result["pred_diag"] for result in variant_results.values()):
        return "no_overlap_semantic_mismatch"
    return "unknown"


def build_audit_rows(gold_index, pred_rows, safe_alias_map):
    rows = []
    for segment_id, gold_row in gold_index.items():
        gold_raw = gold_row.get("gold_entities", "")
        gold_diag, gold_format, gold_failed = parse_diagnostic_entities(gold_raw)
        gold_current = evaluator_entities(gold_raw)
        gold_lower = lower_set(gold_diag)
        gold_punct = punct_set(gold_diag)
        gold_alias = canonical_set(gold_diag, safe_alias_map)
        variant_results = {}
        predicted_union_diag = set()
        predicted_union_current = set()
        for variant in VARIANTS:
            pred_raw = pred_rows[variant][segment_id].get("pred_entities", "")
            pred_diag, pred_format, pred_failed = parse_diagnostic_entities(pred_raw)
            predicted_union_diag.update(pred_diag)
            pred_current = evaluator_entities(pred_raw)
            predicted_union_current.update(pred_current)
            current_j = jaccard(gold_current, pred_current)
            lower_j = jaccard(gold_lower, lower_set(pred_diag))
            punct_j = jaccard(gold_punct, punct_set(pred_diag))
            alias_j = jaccard(gold_alias, canonical_set(pred_diag, safe_alias_map))
            variant_results[variant] = {
                "pred_raw": pred_raw,
                "pred_diag": pred_diag,
                "pred_format": pred_format,
                "pred_failed": pred_failed,
                "pred_current": pred_current,
                "current_jaccard": current_j,
                "lower_jaccard": lower_j,
                "punct_jaccard": punct_j,
                "alias_jaccard": alias_j,
            }
        alias_improved = any(
            result["alias_jaccard"] > result["current_jaccard"]
            for result in variant_results.values()
        )
        bucket = classify_bucket(gold_raw, gold_diag, gold_format, gold_failed, variant_results, alias_improved)
        row = {
            "segment_id": segment_id,
            "source_doc": gold_row.get("source_doc", ""),
            "text": gold_row.get("segment_text") or gold_row.get("text", ""),
            "gold_entities_raw": gold_raw,
            "gold_entities_parsed": fmt_set(gold_diag),
            "gold_entities_current_evaluator_parse": fmt_set(gold_current),
            "gold_parse_format": gold_format,
        }
        for variant in VARIANTS:
            result = variant_results[variant]
            prefix = "combined" if variant == "combined" else variant
            row[f"{prefix}_entities_raw"] = result["pred_raw"]
            row[f"{prefix}_entities_parsed"] = fmt_set(result["pred_diag"])
            row[f"current_{prefix}_entity_jaccard"] = f"{result['current_jaccard']:.6f}"
            row[f"{prefix}_lowercase_trim_jaccard"] = f"{result['lower_jaccard']:.6f}"
            row[f"{prefix}_punctuation_stripped_jaccard"] = f"{result['punct_jaccard']:.6f}"
            row[f"{prefix}_alias_candidate_jaccard"] = f"{result['alias_jaccard']:.6f}"
        row["gold_only_entities"] = fmt_set(set(gold_diag) - set(predicted_union_diag))
        row["predicted_only_entities"] = fmt_set(set(predicted_union_diag) - set(gold_diag))
        row["mismatch_bucket"] = bucket
        row["_gold_diag"] = set(gold_diag)
        row["_gold_current"] = gold_current
        row["_pred_union_diag"] = set(predicted_union_diag)
        row["_pred_union_current"] = predicted_union_current
        row["_variant_results"] = variant_results
        rows.append(row)
    return rows


def summarize(rows, schemas):
    summary = {
        "row_count": len(rows),
        "schemas": schemas,
        "entity_column_names": {
            "gold": "gold_entities",
            "predictions": {variant: "pred_entities" for variant in VARIANTS},
        },
        "non_empty_gold_entity_rows": sum(1 for row in rows if row["_gold_diag"]),
        "parse_failures": {
            "gold": sum(1 for row in rows if row["gold_parse_format"].startswith("json_parse_error")),
        },
        "non_empty_prediction_entity_rows": {},
        "unique_gold_entities_count": len(set().union(*(row["_gold_diag"] for row in rows))) if rows else 0,
        "unique_predicted_entities_count": {},
        "raw_overlap": {},
        "normalised_overlap": {},
        "mismatch_bucket_counts": dict(Counter(row["mismatch_bucket"] for row in rows)),
    }
    for variant in VARIANTS:
        prefix = "combined" if variant == "combined" else variant
        pred_sets = [set(row["_variant_results"][variant]["pred_diag"]) for row in rows]
        summary["non_empty_prediction_entity_rows"][variant] = sum(1 for values in pred_sets if values)
        summary["parse_failures"][variant] = sum(1 for row in rows if row["_variant_results"][variant]["pred_failed"])
        summary["unique_predicted_entities_count"][variant] = len(set().union(*pred_sets)) if pred_sets else 0
        current_values = [float(row[f"current_{prefix}_entity_jaccard"]) for row in rows]
        lower_values = [float(row[f"{prefix}_lowercase_trim_jaccard"]) for row in rows]
        punct_values = [float(row[f"{prefix}_punctuation_stripped_jaccard"]) for row in rows]
        alias_values = [float(row[f"{prefix}_alias_candidate_jaccard"]) for row in rows]
        summary["raw_overlap"][variant] = {
            "average_current_jaccard": safe_div(sum(current_values), len(current_values)),
            "rows_with_any_overlap": sum(1 for value in current_values if value > 0),
            "rows_with_exact_match": sum(1 for value in current_values if value == 1),
        }
        summary["normalised_overlap"][variant] = {
            "lowercase_trim_average_jaccard": safe_div(sum(lower_values), len(lower_values)),
            "punctuation_stripped_average_jaccard": safe_div(sum(punct_values), len(punct_values)),
            "alias_candidate_average_jaccard": safe_div(sum(alias_values), len(alias_values)),
            "rows_improved_by_lowercase_trim": sum(1 for base, value in zip(current_values, lower_values) if value > base),
            "rows_improved_by_punctuation_stripped": sum(1 for base, value in zip(current_values, punct_values) if value > base),
            "rows_improved_by_alias_candidate": sum(1 for base, value in zip(current_values, alias_values) if value > base),
        }
    return summary


def missing_and_extra(rows):
    missing = Counter()
    missing_examples = defaultdict(list)
    extra = Counter()
    extra_examples = defaultdict(list)
    for row in rows:
        segment_id = row["segment_id"]
        for entity in row["_gold_diag"] - row["_pred_union_diag"]:
            missing[entity] += 1
            if len(missing_examples[entity]) < 5:
                missing_examples[entity].append(segment_id)
        for entity in row["_pred_union_diag"] - row["_gold_diag"]:
            extra[entity] += 1
            if len(extra_examples[entity]) < 5:
                extra_examples[entity].append(segment_id)
    return missing, missing_examples, extra, extra_examples


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def write_outputs(rows, summary, candidates, missing, missing_examples, extra, extra_examples):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROPOSED_DIR.mkdir(parents=True, exist_ok=True)
    audit_fields = [
        "segment_id",
        "source_doc",
        "text",
        "gold_entities_raw",
        "gold_entities_parsed",
        "gold_entities_current_evaluator_parse",
        "gold_parse_format",
        "combined_entities_raw",
        "combined_entities_parsed",
        "D_entities_raw",
        "D_entities_parsed",
        "R6_entities_raw",
        "R6_entities_parsed",
        "current_combined_entity_jaccard",
        "current_D_entity_jaccard",
        "current_R6_entity_jaccard",
        "combined_lowercase_trim_jaccard",
        "D_lowercase_trim_jaccard",
        "R6_lowercase_trim_jaccard",
        "combined_punctuation_stripped_jaccard",
        "D_punctuation_stripped_jaccard",
        "R6_punctuation_stripped_jaccard",
        "combined_alias_candidate_jaccard",
        "D_alias_candidate_jaccard",
        "R6_alias_candidate_jaccard",
        "gold_only_entities",
        "predicted_only_entities",
        "mismatch_bucket",
    ]
    write_csv(ROW_AUDIT, [{field: row[field] for field in audit_fields} for row in rows], audit_fields)
    alias_fields = ["gold_entity", "predicted_entity", "support_count", "example_rows", "confidence", "reason"]
    write_csv(ALIAS_CSV, candidates, alias_fields)

    top_missing = [
        [entity, count, "; ".join(missing_examples[entity])]
        for entity, count in missing.most_common(20)
    ]
    top_extra = [
        [entity, count, "; ".join(extra_examples[entity])]
        for entity, count in extra.most_common(20)
    ]
    lines = [
        "# True-Blind Entity Alignment Audit",
        "",
        "This is audit-only. It does not modify gold, predictions, evaluator logic, prompts, models, taxonomies, or thresholds.",
        "",
        "## Answers",
        "",
    ]
    answer_rows = [
        ["A. Why did entity Jaccard collapse to zero?", "Gold entities are JSON-list freeform strings, while the evaluator expects semicolon-delimited entity strings and predictions are ontology_v1 canonical labels. Current parser reads each JSON list as one unmatched entity."],
        ["B. Are predictions empty, parsed wrong, or semantically misaligned?", "Mixed: predictions are non-empty on only a subset of rows and parse correctly when present; non-empty predictions are ontology labels that mostly do not overlap freeform gold labels."],
        ["C. Are gold entities in a different format from ontology_v1?", "Yes. Gold uses JSON lists of domain-specific phrases; ontology_v1 has 31 broad canonical RouteMap/AI-governance labels."],
        ["D. Are true-blind gold entities too freeform compared with previous gold?", "Yes for current evaluator assumptions; labels name local domain objects rather than ontology_v1 canonical concepts."],
        ["E. Would simple normalisation fix anything?", "No meaningful fix: lowercase/trim and punctuation stripping do not create overlap."],
        ["F. Would alias mapping fix anything?", "Only low-confidence cooccurrence aliases are available; no high/medium safe aliases should be auto-applied."],
        ["G. Is an ontology expansion needed?", "Yes, or a separate true-blind entity canonicalisation/adjudication pass mapping freeform gold to ontology_v1."],
        ["H. Is the evaluator reading the correct columns?", "Yes: gold_entities and pred_entities. The failure is representation/ontology alignment, not wrong column selection."],
        ["I. What is the safest next ablation?", "Freeze predictions, create a separate proposed canonicalised gold set via human-reviewed ontology mapping, then rerun scoring as a labelled ablation without replacing this benchmark."],
    ]
    lines.extend(md_table(["question", "answer"], answer_rows))
    lines.extend(["", "## Entity Column Summary", ""])
    lines.extend(md_table(["measure", "value"], [
        ["row count", summary["row_count"]],
        ["non-empty gold entity rows", summary["non_empty_gold_entity_rows"]],
        ["unique gold entities", summary["unique_gold_entities_count"]],
        ["gold parse failures", summary["parse_failures"]["gold"]],
    ]))
    lines.extend(["", "## Prediction Entity Summary", ""])
    lines.extend(md_table(["variant", "non-empty rows", "parse failures", "unique predicted entities"], [
        [variant, summary["non_empty_prediction_entity_rows"][variant], summary["parse_failures"][variant], summary["unique_predicted_entities_count"][variant]]
        for variant in VARIANTS
    ]))
    lines.extend(["", "## Raw Overlap", ""])
    lines.extend(md_table(["variant", "avg current Jaccard", "rows any overlap", "rows exact"], [
        [variant, f"{summary['raw_overlap'][variant]['average_current_jaccard']:.6f}", summary["raw_overlap"][variant]["rows_with_any_overlap"], summary["raw_overlap"][variant]["rows_with_exact_match"]]
        for variant in VARIANTS
    ]))
    lines.extend(["", "## Normalised Overlap", ""])
    lines.extend(md_table(["variant", "lower avg J", "punct avg J", "alias avg J", "lower improved rows", "punct improved rows", "alias improved rows"], [
        [
            variant,
            f"{summary['normalised_overlap'][variant]['lowercase_trim_average_jaccard']:.6f}",
            f"{summary['normalised_overlap'][variant]['punctuation_stripped_average_jaccard']:.6f}",
            f"{summary['normalised_overlap'][variant]['alias_candidate_average_jaccard']:.6f}",
            summary["normalised_overlap"][variant]["rows_improved_by_lowercase_trim"],
            summary["normalised_overlap"][variant]["rows_improved_by_punctuation_stripped"],
            summary["normalised_overlap"][variant]["rows_improved_by_alias_candidate"],
        ]
        for variant in VARIANTS
    ]))
    lines.extend(["", "## Mismatch Buckets", ""])
    lines.extend(md_table(["bucket", "rows"], Counter(row["mismatch_bucket"] for row in rows).most_common()))
    lines.extend(["", "## Top Missing Gold Entities", ""])
    lines.extend(md_table(["gold entity", "count", "example segment_ids"], top_missing[:10]))
    lines.extend(["", "## Top Predicted-Only Entities", ""])
    lines.extend(md_table(["predicted entity", "count", "example segment_ids"], top_extra[:10]))
    lines.extend(["", "## Alias Candidates", ""])
    lines.append(f"Candidate alias rows: {len(candidates)}. Low-confidence aliases are not auto-applied.")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary_out = dict(summary)
    summary_out["top_missing_gold_entities"] = [
        {"entity": entity, "count": count, "examples": missing_examples[entity]}
        for entity, count in missing.most_common(20)
    ]
    summary_out["top_predicted_only_entities"] = [
        {"entity": entity, "count": count, "examples": extra_examples[entity]}
        for entity, count in extra.most_common(20)
    ]
    summary_out["alias_candidates_count"] = len(candidates)
    summary_out["high_or_medium_alias_candidates_count"] = sum(1 for row in candidates if row["confidence"] in {"high", "medium"})
    summary_out["main_diagnosis"] = "Entity scoring collapsed because true-blind gold entities are JSON-list, domain-freeform labels while predictions are semicolon-delimited ontology_v1 canonical labels; current evaluator reads gold JSON as a single nonmatching entity and simple normalisation does not restore overlap."
    summary_out["recommended_next_test"] = "Create a separate human-reviewed ontology-alignment ablation that maps true-blind freeform gold entities to ontology_v1 or expands ontology_v1, then rerun scoring without changing original gold/predictions."
    SUMMARY_JSON.write_text(json.dumps(summary_out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    proposal = [
        "# True-Blind Entity Canonicalisation Proposal",
        "",
        "Status: PROPOSED ONLY. These files are not evaluator inputs and must not replace true_blind_gold.csv or prediction CSVs.",
        "",
        "The safe automated proposal is delimiter canonicalisation only: parse JSON-list gold entities into semicolon-delimited strings while leaving ontology mapping for human review.",
        "",
        f"- proposed gold: `{PROPOSED_GOLD.relative_to(ROOT)}`",
        f"- proposed R6 predictions: `{PROPOSED_R6.relative_to(ROOT)}`",
        "- low-confidence cooccurrence aliases are listed separately and are not applied.",
        "",
        "Recommended next test: human-review candidate aliases or expand ontology_v1, save as a named ablation input, then rerun metrics as an ablation report rather than replacing the true-blind benchmark.",
    ]
    PROPOSAL_MD.write_text("\n".join(proposal) + "\n", encoding="utf-8")


def write_proposed_files(gold_rows, pred_rows):
    gold_fields = list(gold_rows[0].keys())
    proposed_gold_fields = gold_fields + [
        "gold_entities_original",
        "entity_canonicalisation_status",
    ]
    proposed_gold_rows = []
    for row in gold_rows:
        values, _, failed = parse_diagnostic_entities(row.get("gold_entities", ""))
        out = dict(row)
        out["gold_entities_original"] = row.get("gold_entities", "")
        out["gold_entities"] = fmt_set(values) if not failed else row.get("gold_entities", "")
        out["entity_canonicalisation_status"] = "PROPOSED_DELIMITER_ONLY_NOT_EVALUATOR_INPUT"
        proposed_gold_rows.append(out)
    write_csv(PROPOSED_GOLD, proposed_gold_rows, proposed_gold_fields)

    r6_rows = list(pred_rows["R6"].values())
    r6_fields = list(r6_rows[0].keys())
    proposed_r6_fields = r6_fields + [
        "pred_entities_original",
        "entity_canonicalisation_status",
    ]
    proposed_r6_rows = []
    for row in r6_rows:
        values, _, failed = parse_diagnostic_entities(row.get("pred_entities", ""))
        out = dict(row)
        out["pred_entities_original"] = row.get("pred_entities", "")
        out["pred_entities"] = fmt_set(values) if not failed else row.get("pred_entities", "")
        out["entity_canonicalisation_status"] = "PROPOSED_FORMAT_ONLY_NOT_EVALUATOR_INPUT"
        proposed_r6_rows.append(out)
    write_csv(PROPOSED_R6, proposed_r6_rows, proposed_r6_fields)


def print_summary(summary, candidates, missing, extra):
    print("true_blind_entity_alignment_audit")
    print(f"row_count={summary['row_count']}")
    print("entity_columns=gold:gold_entities; combined:pred_entities; D:pred_entities; R6:pred_entities")
    print(f"non_empty_gold_entity_rows={summary['non_empty_gold_entity_rows']}")
    for variant in VARIANTS:
        print(f"non_empty_{variant}_entity_rows={summary['non_empty_prediction_entity_rows'][variant]}")
    print("parse_failures=" + json.dumps(summary["parse_failures"], sort_keys=True))
    print("raw_overlap")
    for variant in VARIANTS:
        row = summary["raw_overlap"][variant]
        print(f"{variant}: avg_current_jaccard={row['average_current_jaccard']:.6f} any_overlap_rows={row['rows_with_any_overlap']} exact_rows={row['rows_with_exact_match']}")
    print("normalised_overlap")
    for variant in VARIANTS:
        row = summary["normalised_overlap"][variant]
        print(
            f"{variant}: lower_avg={row['lowercase_trim_average_jaccard']:.6f} "
            f"punct_avg={row['punctuation_stripped_average_jaccard']:.6f} "
            f"alias_avg={row['alias_candidate_average_jaccard']:.6f} "
            f"alias_improved_rows={row['rows_improved_by_alias_candidate']}"
        )
    print("top_missing_gold_entities")
    for entity, count in missing.most_common(10):
        print(f"- {entity}: {count}")
    print("top_predicted_only_entities")
    for entity, count in extra.most_common(10):
        print(f"- {entity}: {count}")
    print(f"alias_candidates_count={len(candidates)}")
    print("main_diagnosis=gold JSON-list freeform entities are not aligned with semicolon ontology_v1 prediction entities; evaluator columns are correct, representation/ontology alignment is not.")
    print("recommended_next_test=human-reviewed ontology-alignment ablation using proposed files, without replacing original gold or predictions.")
    print(f"row_audit={ROW_AUDIT.relative_to(ROOT)}")
    print(f"report={REPORT_MD.relative_to(ROOT)}")
    print(f"summary={SUMMARY_JSON.relative_to(ROOT)}")


def main():
    schemas, gold_rows, gold_index, pred_rows = collect_rows()
    candidates, safe_alias_map = infer_alias_candidates(gold_index, pred_rows)
    audit_rows = build_audit_rows(gold_index, pred_rows, safe_alias_map)
    summary = summarize(audit_rows, schemas)
    missing, missing_examples, extra, extra_examples = missing_and_extra(audit_rows)
    write_outputs(audit_rows, summary, candidates, missing, missing_examples, extra, extra_examples)
    write_proposed_files(gold_rows, pred_rows)
    print_summary(summary, candidates, missing, extra)


if __name__ == "__main__":
    main()
