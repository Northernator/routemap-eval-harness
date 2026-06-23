import argparse
import argparse
import csv
import json
import re
import urllib.error
from pathlib import Path

from entity_matchers_diagnostic import EmbeddingMatcher, difflib_similarity, normalized_exact_similarity, score_pair, score_rows
from extract_entities_domain_general_v1 import extract_entities, write_predictions
from run_live_llm_provider import request_json


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "data/v1/true_blind_natural_language/ablations/domain_general_entity_extractor_v1"
PRED_DIR = OUT_ROOT / "predictions"
ROWS_DIR = OUT_ROOT / "rows"
REPORT_MD = OUT_ROOT / "DOMAIN_GENERAL_ENTITY_EXTRACTOR_V1_REPORT.md"
SUMMARY_JSON = OUT_ROOT / "DOMAIN_GENERAL_ENTITY_EXTRACTOR_V1_SUMMARY.json"
GOLD_PATH = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
ONTOLOGY_REF = ROOT / "data/v1/true_blind_natural_language/predictions/combined_v3_true_blind_predictions.csv"
HEADROOM_CEILING = 0.9885714285714285


def clean(value):
    return "" if value is None else str(value).strip()


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
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


def index_by_segment(rows):
    return {row["segment_id"]: row for row in rows}


def build_deterministic_predictions():
    outputs = {}
    for variant in ["proper_quoted", "noun_chunks_topk"]:
        out = PRED_DIR / f"{variant}_predictions.csv"
        write_predictions(GOLD_PATH, variant, out)
        outputs[variant] = out
    return outputs


def extract_json_array(text):
    value = "" if text is None else str(text)
    fence = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", value, flags=re.IGNORECASE | re.DOTALL)
    candidates = []
    if fence:
        candidates.append(fence.group(1))
    start = value.find("[")
    while start != -1:
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(value)):
            char = value[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    candidates.append(value[start:index + 1])
                    break
        start = value.find("[", start + 1)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return [clean(item) for item in parsed if clean(item)]
        except json.JSONDecodeError:
            continue
    return []


def run_llm_predictions():
    rows = read_csv(GOLD_PATH)
    out_path = PRED_DIR / "llm_ollama_predictions.csv"
    host = "http://localhost:11434"
    prompt_template = (
        "List the key entities, systems, roles, and objects explicitly named in this passage. "
        "Return a JSON array of short verbatim noun phrases, no commentary.\n\nPassage:\n{text}"
    )
    out_rows = []
    try:
        for row in rows:
            text = row.get("segment_text") or row.get("text", "")
            response = request_json(
                f"{host}/api/generate",
                {"model": "llama3.1:latest", "prompt": prompt_template.format(text=text), "stream": False},
                timeout=120,
            )
            entities = extract_json_array(response.get("response", ""))
            out_rows.append({
                "segment_id": row["segment_id"],
                "segment_text": text,
                "gold_entities": row.get("gold_entities", ""),
                "pred_entities": "; ".join(entities),
            })
    except (urllib.error.URLError, TimeoutError, RuntimeError, OSError) as exc:
        return None, f"llm_ollama skipped: {exc}"
    write_csv(out_path, out_rows, ["segment_id", "segment_text", "gold_entities", "pred_entities"])
    return out_path, "llm_ollama ran"


def load_reference_predictions():
    gold_rows = index_by_segment(read_csv(GOLD_PATH))
    ref_rows = read_csv(ONTOLOGY_REF)
    out_rows = []
    for row in ref_rows:
        gold = gold_rows[row["segment_id"]]
        out_rows.append({
            "segment_id": row["segment_id"],
            "segment_text": gold.get("segment_text") or gold.get("text", ""),
            "gold_entities": gold.get("gold_entities", ""),
            "pred_entities": row.get("pred_entities", ""),
        })
    out_path = PRED_DIR / "ontology_v1_reference_predictions.csv"
    write_csv(out_path, out_rows, ["segment_id", "segment_text", "gold_entities", "pred_entities"])
    return out_path


def load_pairs(path):
    rows = read_csv(path)
    parsed = []
    for row in rows:
        parsed.append({
            "segment_id": row["segment_id"],
            "gold_entities": parse_gold_entities(row.get("gold_entities", "")),
            "pred_entities": parse_pred_entities(row.get("pred_entities", "")),
            "segment_text": row.get("segment_text", ""),
        })
    return parsed


def row_pairs(rows):
    return [(row["gold_entities"], row["pred_entities"]) for row in rows]


def mean_preds(rows):
    return sum(len(row["pred_entities"]) for row in rows) / len(rows) if rows else 0.0


def write_row_scores(variant, matcher_name, threshold, rows, similarity_fn):
    out_rows = []
    for row in rows:
        scored = score_pair(row["gold_entities"], row["pred_entities"], similarity_fn, threshold)
        out_rows.append({
            "variant": variant,
            "matcher": matcher_name,
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
    filename = f"{variant}_{matcher_name}_t{str(threshold).replace('.', 'p')}.csv"
    write_csv(ROWS_DIR / filename, out_rows, list(out_rows[0].keys()) if out_rows else ["variant"])


def score_variant(variant, path, embedding):
    rows = load_pairs(path)
    matchers = [
        ("M1_normalized_exact", 1.0, normalized_exact_similarity),
        ("M3_fuzzy_difflib", 0.6, difflib_similarity),
    ]
    if embedding.available:
        values = set()
        for row in rows:
            values.update(row["gold_entities"])
            values.update(row["pred_entities"])
        embedding.prepare(values)
        matchers.append(("M4_embedding_cosine", 0.5, embedding.similarity))
    results = []
    for matcher_name, threshold, similarity_fn in matchers:
        metrics = score_rows(row_pairs(rows), similarity_fn, threshold)
        result = {
            "variant": variant,
            "matcher": matcher_name,
            "threshold": threshold,
            **metrics,
            "mean_preds_per_segment": mean_preds(rows),
        }
        results.append(result)
        write_row_scores(variant, matcher_name, threshold, rows, similarity_fn)
    return results


def best_result(results):
    return max(results, key=lambda row: (row["soft_f1"], row["soft_jaccard"], row["soft_precision"]))


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def recommendation(verdicts, best):
    if verdicts["reaches_in_domain_band"] and verdicts["precision_healthy"]:
        return f"Adopt extractive entity field as next development path, starting from {best['variant']} with fixed dev-set tuning before any fresh blind eval."
    if verdicts["beats_ontology_baseline"]:
        return f"Develop a domain-general extractor on train/dev; {best['variant']} shows feasibility but precision/target-band criteria are not both satisfied."
    return "Current deterministic extractors do not clear feasibility; design a stronger domain-general extractor before rerunning a fresh blind eval."


def write_report(all_results, embedding, llm_status, verdicts, recommendation_text):
    rows = []
    for variant, results in all_results.items():
        for row in results:
            rows.append([
                variant,
                row["matcher"],
                row["threshold"],
                f"{row['soft_f1']:.6f}",
                f"{row['soft_precision']:.6f}",
                f"{row['soft_recall']:.6f}",
                f"{row['soft_jaccard']:.6f}",
                f"{row['mean_preds_per_segment']:.3f}",
            ])
    lines = [
        "# Domain-General Entity Extractor v1",
        "",
        "ABLATION ONLY. Gold is frozen. This is a feasibility read with a priori extractor constants, not a tuned true-blind score.",
        "",
        f"- embedding_axis_ran: {'true' if embedding.available else 'false'}",
        f"- embedding_status: {embedding.reason}",
        f"- llm_status: {llm_status}",
        f"- headroom_ceiling_context: {HEADROOM_CEILING:.6f}",
        "",
        "## Main Table",
        "",
    ]
    lines.extend(md_table(["variant", "matcher", "threshold", "soft_f1", "soft_precision", "soft_recall", "soft_jaccard", "mean_preds_per_seg"], rows))
    lines.extend(["", "## Verdicts", ""])
    lines.extend(md_table(["boolean", "value"], [[key, "YES" if value else "NO"] for key, value in verdicts.items()]))
    lines.extend(["", "## Recommendation", "", recommendation_text])
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_table(all_results):
    print("DOMAIN_GENERAL_ENTITY_EXTRACTOR_V1_SOFT_F1_TABLE")
    print("variant,matcher,threshold,soft_f1,soft_precision,soft_recall,soft_jaccard,mean_preds_per_segment")
    for variant, results in all_results.items():
        for row in results:
            print(",".join([
                variant,
                row["matcher"],
                str(row["threshold"]),
                f"{row['soft_f1']:.6f}",
                f"{row['soft_precision']:.6f}",
                f"{row['soft_recall']:.6f}",
                f"{row['soft_jaccard']:.6f}",
                f"{row['mean_preds_per_segment']:.6f}",
            ]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-llm", action="store_true")
    args = parser.parse_args()

    prediction_paths = build_deterministic_predictions()
    prediction_paths["ontology_v1_reference"] = load_reference_predictions()
    llm_status = "skipped: --with-llm not passed"
    if args.with_llm:
        llm_path, llm_status = run_llm_predictions()
        if llm_path:
            prediction_paths["llm_ollama"] = llm_path

    embedding = EmbeddingMatcher.load()
    all_results = {
        variant: score_variant(variant, path, embedding)
        for variant, path in prediction_paths.items()
    }
    ref_best = best_result(all_results["ontology_v1_reference"])
    best = best_result([row for results in all_results.values() for row in results if row["variant"] != "ontology_v1_reference"])
    verdicts = {
        "beats_ontology_baseline": best["soft_f1"] >= 5 * ref_best["soft_f1"],
        "reaches_in_domain_band": best["soft_f1"] >= 0.23,
        "precision_healthy": best["soft_precision"] >= 0.30,
        "llm_variant_ran": "llm_ollama" in all_results,
    }
    recommendation_text = recommendation(verdicts, best)
    write_report(all_results, embedding, llm_status, verdicts, recommendation_text)
    summary = {
        "ablation": "true_blind_domain_general_entity_extractor_v1",
        "embedding_axis_ran": embedding.available,
        "embedding_status": embedding.reason,
        "llm_status": llm_status,
        "headroom_ceiling_context": HEADROOM_CEILING,
        "results": all_results,
        "best_variant": best,
        "ontology_v1_reference_best": ref_best,
        "verdicts": verdicts,
        "recommendation": recommendation_text,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_table(all_results)
    print("embedding_axis_ran=" + ("true" if embedding.available else "false"))
    print("embedding_status=" + embedding.reason)
    print("llm_status=" + llm_status)
    print("best_variant=" + json.dumps(best, sort_keys=True))
    print("ontology_v1_reference_best=" + json.dumps(ref_best, sort_keys=True))
    print("verdicts=" + json.dumps(verdicts, sort_keys=True))
    print("recommendation=" + recommendation_text)
    print(f"report={REPORT_MD.relative_to(ROOT)}")
    print(f"summary={SUMMARY_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
