import csv
import difflib
import json
from collections import defaultdict
from pathlib import Path

from entity_matchers_diagnostic import (
    EMBEDDING_THRESHOLDS,
    MATCHER_SPECS,
    EmbeddingMatcher,
    difflib_similarity,
    normalize,
    score_pair,
    score_rows,
    token_set,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "data/v1/true_blind_natural_language/ablations/entity_matching_diagnostic_v1"
ROWS_DIR = OUT_ROOT / "rows"
REPORT_MD = OUT_ROOT / "ENTITY_MATCHING_DIAGNOSTIC_V1_REPORT.md"
SUMMARY_JSON = OUT_ROOT / "ENTITY_MATCHING_DIAGNOSTIC_V1_SUMMARY.json"
GOLD_PATH = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
PREDICTIONS = {
    "combined_v3": ROOT / "data/v1/true_blind_natural_language/predictions/combined_v3_true_blind_predictions.csv",
    "D": ROOT / "data/v1/true_blind_natural_language/predictions/D_true_blind_predictions.csv",
    "R6": ROOT / "data/v1/true_blind_natural_language/predictions/R6_true_blind_predictions.csv",
}
VARIANTS = ["combined_v3", "D", "R6"]


def clean(value):
    return "" if value is None else str(value).strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_gold_entities(value):
    raw = clean(value)
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [clean(item) for item in parsed if clean(item)]
        except json.JSONDecodeError:
            pass
    delimiter = ";" if ";" in raw else ","
    return [clean(item) for item in raw.split(delimiter) if clean(item)]


def parse_pred_entities(value):
    raw = clean(value)
    if not raw:
        return []
    return [clean(item) for item in raw.split(";") if clean(item)]


def index_rows(rows):
    return {row["segment_id"]: row for row in rows}


def load_pairs():
    gold_rows = read_csv(GOLD_PATH)
    gold_by_id = index_rows(gold_rows)
    variant_rows = {variant: index_rows(read_csv(path)) for variant, path in PREDICTIONS.items()}
    rows = {}
    for variant in VARIANTS:
        rows[variant] = []
        for segment_id, gold_row in gold_by_id.items():
            pred_row = variant_rows[variant][segment_id]
            rows[variant].append({
                "segment_id": segment_id,
                "segment_text": gold_row.get("segment_text") or gold_row.get("text", ""),
                "gold_entities": parse_gold_entities(gold_row.get("gold_entities", "")),
                "pred_entities": parse_pred_entities(pred_row.get("pred_entities", "")),
                "pred_valid": pred_row.get("pred_valid", ""),
            })
    return rows


def row_pairs(rows, population):
    if population == "scored_rows":
        selected = [row for row in rows if row["pred_valid"] == "YES"]
    elif population == "all_gold_rows":
        selected = list(rows)
    else:
        raise ValueError(population)
    return selected, [(row["gold_entities"], row["pred_entities"]) for row in selected]


def matcher_id(name, threshold):
    return f"{name}_t{threshold}".replace(".", "p")


def write_row_scores(variant, population, name, threshold, rows, similarity_fn):
    out_rows = []
    for row in rows:
        scored = score_pair(row["gold_entities"], row["pred_entities"], similarity_fn, threshold)
        out_rows.append({
            "variant": variant,
            "population": population,
            "matcher": name,
            "threshold": threshold,
            "segment_id": row["segment_id"],
            "gold_entities": "; ".join(row["gold_entities"]),
            "pred_entities": "; ".join(row["pred_entities"]),
            "gold_count": scored["gold_count"],
            "pred_count": scored["pred_count"],
            "matches": scored["matches"],
            "soft_precision": f"{scored['soft_precision']:.6f}",
            "soft_recall": f"{scored['soft_recall']:.6f}",
            "soft_f1": f"{scored['soft_f1']:.6f}",
            "soft_jaccard": f"{scored['soft_jaccard']:.6f}",
            "matched_pairs": json.dumps(scored["matched_pairs"], ensure_ascii=False),
        })
    filename = f"{variant}_{population}_{matcher_id(name, threshold)}.csv"
    write_csv(ROWS_DIR / filename, out_rows, list(out_rows[0].keys()) if out_rows else ["variant"])


def collect_all_entity_strings(rows_by_variant):
    values = set()
    for rows in rows_by_variant.values():
        for row in rows:
            values.update(row["gold_entities"])
            values.update(row["pred_entities"])
    return values


def run_matchers(rows_by_variant):
    embedding = EmbeddingMatcher.load()
    if embedding.available:
        embedding.prepare(collect_all_entity_strings(rows_by_variant))
    specs = list(MATCHER_SPECS)
    if embedding.available:
        for threshold in EMBEDDING_THRESHOLDS:
            specs.append({
                "name": "M4_embedding_cosine",
                "threshold": threshold,
                "kind": "embedding",
                "similarity": embedding.similarity,
            })
    results = {}
    for population in ["all_gold_rows", "scored_rows"]:
        results[population] = {}
        for variant, rows in rows_by_variant.items():
            selected, pairs = row_pairs(rows, population)
            results[population][variant] = []
            for spec in specs:
                metrics = score_rows(pairs, spec["similarity"], spec["threshold"])
                record = {
                    "matcher": spec["name"],
                    "threshold": spec["threshold"],
                    "kind": spec["kind"],
                    **metrics,
                }
                results[population][variant].append(record)
                write_row_scores(variant, population, spec["name"], spec["threshold"], selected, spec["similarity"])
    return results, embedding


def ngrams(tokens, min_n, max_n):
    for n in range(max(1, min_n), max_n + 1):
        for index in range(0, max(0, len(tokens) - n + 1)):
            yield " ".join(tokens[index:index + n])


def text_present(entity, text):
    entity_norm = normalize(entity)
    text_norm = normalize(text)
    if not entity_norm:
        return False
    if entity_norm in text_norm:
        return True
    entity_len = max(1, len(entity_norm.split()))
    tokens = text_norm.split()
    for gram in ngrams(tokens, max(1, entity_len - 1), min(len(tokens), entity_len + 1)):
        if difflib.SequenceMatcher(None, entity_norm, gram).ratio() >= 0.8:
            return True
    return False


def prediction_captures(entity, pred_entities):
    return any(difflib_similarity(entity, pred) >= 0.8 for pred in pred_entities)


def headroom(rows_by_variant):
    base_rows = rows_by_variant["combined_v3"]
    total = 0
    present = 0
    captured_by_variant = {variant: 0 for variant in VARIANTS}
    for index, row in enumerate(base_rows):
        for entity in row["gold_entities"]:
            total += 1
            if text_present(entity, row["segment_text"]):
                present += 1
            for variant in VARIANTS:
                if prediction_captures(entity, rows_by_variant[variant][index]["pred_entities"]):
                    captured_by_variant[variant] += 1
    frac_present = present / total if total else 0.0
    by_variant = {
        variant: {
            "frac_gold_captured_by_prediction": captured / total if total else 0.0,
            "headroom_gap": frac_present - (captured / total if total else 0.0),
        }
        for variant, captured in captured_by_variant.items()
    }
    max_captured = max(item["frac_gold_captured_by_prediction"] for item in by_variant.values()) if by_variant else 0.0
    return {
        "gold_entities_total": total,
        "frac_gold_text_present": frac_present,
        "frac_gold_captured_by_prediction_max_variant": max_captured,
        "headroom_gap_max_variant": frac_present - max_captured,
        "by_variant": by_variant,
    }


def best_record(results, population, variant, include_embedding=True):
    rows = [
        row for row in results[population][variant]
        if include_embedding or row["kind"] != "embedding"
    ]
    return max(rows, key=lambda row: (row["soft_jaccard"], row["soft_f1"], -float(row["threshold"])))


def best_surface(results, population="all_gold_rows"):
    rows = []
    for variant in VARIANTS:
        rows.extend([row for row in results[population][variant] if row["kind"] == "surface"])
    return max(rows, key=lambda row: (row["soft_jaccard"], row["soft_f1"], -float(row["threshold"])))


def best_embedding(results, population="all_gold_rows"):
    rows = []
    for variant in VARIANTS:
        rows.extend([row for row in results[population][variant] if row["kind"] == "embedding"])
    return max(rows, key=lambda row: (row["soft_jaccard"], row["soft_f1"], -float(row["threshold"]))) if rows else None


def verdicts(results, headroom_stats, embedding_available):
    surface = best_surface(results)
    embedding = best_embedding(results)
    best_all = embedding if embedding and embedding["soft_jaccard"] > surface["soft_jaccard"] else surface
    synonymy_gap = bool(embedding and embedding["soft_jaccard"] - surface["soft_jaccard"] >= 0.10)
    captured = headroom_stats["frac_gold_captured_by_prediction_max_variant"]
    return {
        "metric_brittleness_significant": surface["soft_jaccard"] >= 0.23,
        "synonymy_gap": synonymy_gap,
        "extractor_failure_dominant": best_all["soft_jaccard"] < 0.15 and headroom_stats["frac_gold_text_present"] >= 0.5 and captured < 0.15,
        "embedding_axis_ran": embedding_available,
    }


def recommendation(flags):
    if flags["metric_brittleness_significant"]:
        return "adopt a soft entity metric as a named ablation; surface matching recovers substantial overlap."
    if flags["synonymy_gap"]:
        return "adopt a soft semantic entity metric and validate embeddings under a frozen offline model."
    if flags["extractor_failure_dominant"]:
        return "pursue a domain-general entity extractor; current predictions do not recover gold entities even under relaxed matching."
    return "pursue both soft metrics and a domain-general extractor; current evidence is mixed."


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def matcher_table(results, population):
    rows = []
    for variant in VARIANTS:
        for row in results[population][variant]:
            rows.append([
                row["matcher"],
                row["threshold"],
                variant,
                f"{row['soft_jaccard']:.6f}",
                f"{row['soft_f1']:.6f}",
            ])
    return rows


def write_report(results, headroom_stats, embedding, flags, recommendation_text):
    lines = [
        "# Entity Matching Diagnostic v1",
        "",
        "ABLATION ONLY. Gold is frozen; this diagnostic must not tune or promote the locked true-blind test, prompts, taxonomies, thresholds, ontology, evaluator, or R6.",
        "",
        f"- embedding_axis_ran: {'true' if embedding.available else 'false'}",
        f"- embedding_skip_reason: {embedding.reason}",
        "",
        "## All Gold Rows",
        "",
    ]
    lines.extend(md_table(["matcher", "threshold", "variant", "soft_jaccard", "soft_f1"], matcher_table(results, "all_gold_rows")))
    lines.extend(["", "## Scored Rows", ""])
    lines.extend(md_table(["matcher", "threshold", "variant", "soft_jaccard", "soft_f1"], matcher_table(results, "scored_rows")))
    lines.extend(["", "## Headroom", ""])
    headroom_rows = [
        [
            variant,
            headroom_stats["gold_entities_total"],
            f"{headroom_stats['frac_gold_text_present']:.6f}",
            f"{headroom_stats['by_variant'][variant]['frac_gold_captured_by_prediction']:.6f}",
            f"{headroom_stats['by_variant'][variant]['headroom_gap']:.6f}",
        ]
        for variant in VARIANTS
    ]
    lines.extend(md_table(["variant", "gold_entities_total", "frac_gold_text_present", "frac_gold_captured_by_prediction", "headroom_gap"], headroom_rows))
    lines.extend(["", "## Verdicts", ""])
    lines.extend(md_table(["boolean", "value"], [[key, "YES" if value else "NO"] for key, value in flags.items()]))
    lines.extend(["", "## Recommendation", "", recommendation_text])
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(results, headroom_stats, embedding, flags, recommendation_text):
    summary = {
        "ablation": "true_blind_entity_matching_diagnostic_v1",
        "embedding_axis_ran": embedding.available,
        "embedding_skip_reason": embedding.reason,
        "results": results,
        "headroom": headroom_stats,
        "verdicts": flags,
        "recommendation": recommendation_text,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_main_table(results):
    print("ENTITY_MATCHING_DIAGNOSTIC_V1_ALL_GOLD_ROWS")
    print("matcher,threshold,variant,soft_jaccard,soft_f1")
    for row in matcher_table(results, "all_gold_rows"):
        print(",".join(str(value) for value in row))


def main():
    rows_by_variant = load_pairs()
    results, embedding = run_matchers(rows_by_variant)
    headroom_stats = headroom(rows_by_variant)
    flags = verdicts(results, headroom_stats, embedding.available)
    recommendation_text = recommendation(flags)
    write_report(results, headroom_stats, embedding, flags, recommendation_text)
    write_summary(results, headroom_stats, embedding, flags, recommendation_text)
    print_main_table(results)
    print("embedding_axis_ran=" + ("true" if embedding.available else "false"))
    print("embedding_reason=" + embedding.reason)
    print("headroom=" + json.dumps(headroom_stats, sort_keys=True))
    print("verdicts=" + json.dumps(flags, sort_keys=True))
    print("recommendation=" + recommendation_text)
    print(f"report={REPORT_MD.relative_to(ROOT)}")
    print(f"summary={SUMMARY_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
