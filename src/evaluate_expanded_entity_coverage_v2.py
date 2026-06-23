import csv
from collections import Counter
from pathlib import Path

from entity_extractor_v2 import extract_entities_v2
from entity_ontology_v1 import extract_entities_ontology_v1, split_entity_set


EXP_TRAIN = Path("data/v1/gold/expanded_train_v2.csv")
LOCKED_TEST = Path("data/v1/gold/model_test_fresh_adjudicated_role.csv")
EXP_TEST = Path("data/v1/gold/expanded_test_v2.csv")
OUT_CSV = Path("data/v1/gold/expanded_entity_baseline_results_v2.csv")
OUT_MD = Path("data/v1/gold/EXPANDED_ENTITY_BASELINE_RESULTS_V2.md")
PHASE_REPORT = Path("data/v1/gold/PARALLEL_PHASE_A_B_REPORT.md")


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(a, b):
    return a / b if b else 0.0


def build_gazetteer(train_rows):
    entities = sorted({entity.strip() for row in train_rows for entity in row.get("gold_entities", "").split(";") if entity.strip()})
    return entities


def gazetteer_extract(text, title, entities):
    haystack = f"{title} {text}".lower()
    found = []
    for entity in entities:
        tokens = [token for token in entity.lower().replace("-", " ").split() if len(token) > 2]
        if entity.lower() in haystack or (tokens and all(token in haystack for token in tokens[:2])):
            found.append(entity)
    return "; ".join(found)


def score(gold, pred):
    inter = gold & pred
    union = gold | pred
    precision = safe_div(len(inter), len(pred))
    recall = safe_div(len(inter), len(gold))
    f1 = safe_div(2 * precision * recall, precision + recall)
    return gold == pred, safe_div(len(inter), len(union)), precision, recall, f1, not inter, gold - pred, pred - gold


def evaluate(rows, model_name, extractor):
    totals = Counter()
    missing = Counter()
    extra = Counter()
    for row in rows:
        gold = split_entity_set(row.get("gold_entities", ""))
        pred = split_entity_set(extractor(row.get("text", ""), row.get("title", "")))
        exact, jaccard, precision, recall, f1, zero, miss, ext = score(gold, pred)
        totals["exact"] += int(exact)
        totals["jaccard"] += jaccard
        totals["precision"] += precision
        totals["recall"] += recall
        totals["f1"] += f1
        totals["zero"] += int(zero)
        missing.update(miss)
        extra.update(ext)
    n = len(rows)
    return {
        "model": model_name,
        "exact": safe_div(totals["exact"], n),
        "jaccard": safe_div(totals["jaccard"], n),
        "precision": safe_div(totals["precision"], n),
        "recall": safe_div(totals["recall"], n),
        "f1": safe_div(totals["f1"], n),
        "zero": totals["zero"],
        "missing": missing,
        "extra": extra,
    }


def best_role_summary():
    path = Path("data/v1/gold/expanded_role_baseline_results_v2.csv")
    if not path.exists():
        return {}
    rows = read_rows(path)
    best = {}
    for testset in ["locked_fresh_adjudicated", "expanded_test_v2"]:
        candidates = [row for row in rows if row["testset"] == testset and row["metric"] == "fine_8_accuracy"]
        best[testset] = max(candidates, key=lambda row: float(row["value"]))
    return best


def write_phase_report(entity_best, role_best, split_counts):
    lines = [
        "# Parallel Phase A/B Report",
        "",
        "## Why This Phase Exists",
        "",
        "RouteMap v1 showed measurable coarse route signal but weak exact full extraction. This phase prepares a provider-ready extractor path while expanding development data for boundary and entity coverage.",
        "",
        "## Phase A Outputs",
        "",
        "- JSON extraction contract: `src/routemap_extraction_contract.py`",
        "- Provider interface: `src/routemap_extractor_provider.py`",
        "- Offline rule provider and prompt-only provider",
        "- Rule provider report: `data/v1/gold/ROUTEMAP_EXTRACTOR_RULE_PROVIDER_RESULTS.md`",
        "",
        "## Phase B Outputs",
        "",
        "- Expanded dataset size: 560 rows",
        f"- Split sizes: train {split_counts.get('train', 0)}, dev {split_counts.get('dev', 0)}, test {split_counts.get('test', 0)}",
        "- Coverage: 400 boundary-pair rows plus 160 entity-focused rows",
        "- Role report: `data/v1/gold/EXPANDED_ROLE_BASELINE_RESULTS_V2.md`",
        "- Entity report: `data/v1/gold/EXPANDED_ENTITY_BASELINE_RESULTS_V2.md`",
        "",
        "## Expanded Data Impact",
        "",
    ]
    for testset, row in role_best.items():
        lines.append(f"- Best role model on {testset}: `{row['setting']}` / `{row['model']}` fine_8 {float(row['value']):.3f}")
    for testset, result in entity_best.items():
        lines.append(f"- Best entity model on {testset}: `{result['model']}` Jaccard {result['jaccard']:.3f}, F1 {result['f1']:.3f}")
    lines.extend([
        "",
        "## Next Recommendation",
        "",
        "If expanded-data gains transfer to the locked fresh test, use the expansion for the next full extractor development cycle. If gains are mostly internal to expanded_test_v2, move to real LLM provider evaluation with frozen prompts and batch scoring.",
        "",
        "Synthetic expansion is useful for development but must later be replaced or augmented with real documents and human labels.",
    ])
    PHASE_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    train = read_rows(EXP_TRAIN)
    tests = {"locked_fresh_adjudicated": read_rows(LOCKED_TEST), "expanded_test_v2": read_rows(EXP_TEST)}
    gazetteer = build_gazetteer(train)
    extractors = {
        "current_extractor_v2": extract_entities_v2,
        "ontology_v1": extract_entities_ontology_v1,
        "expanded_gazetteer": lambda text, title: gazetteer_extract(text, title, gazetteer),
    }
    result_rows = []
    best = {}
    md = ["# Expanded Entity Baseline Results V2", "", "| testset | model | exact | Jaccard | precision | recall | F1 | zero overlap |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for testset, rows in tests.items():
        results = []
        for name, extractor in extractors.items():
            result = evaluate(rows, name, extractor)
            results.append(result)
            result_rows.append({
                "testset": testset,
                "model": name,
                "exact": f"{result['exact']:.6f}",
                "jaccard": f"{result['jaccard']:.6f}",
                "precision": f"{result['precision']:.6f}",
                "recall": f"{result['recall']:.6f}",
                "f1": f"{result['f1']:.6f}",
                "zero_overlap": str(result["zero"]),
            })
            md.append(f"| {testset} | {name} | {result['exact']:.3f} | {result['jaccard']:.3f} | {result['precision']:.3f} | {result['recall']:.3f} | {result['f1']:.3f} | {result['zero']} |")
        best[testset] = max(results, key=lambda row: (row["jaccard"], row["f1"], row["model"]))
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["testset", "model", "exact", "jaccard", "precision", "recall", "f1", "zero_overlap"])
        writer.writeheader()
        writer.writerows(result_rows)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    split_counts = {name: len(read_rows(Path(f"data/v1/gold/expanded_{name}_v2.csv"))) for name in ["train", "dev", "test"]}
    write_phase_report(best, best_role_summary(), split_counts)
    for testset, result in best.items():
        print(f"Best entity {testset}: {result['model']} Jaccard={result['jaccard']:.3f} F1={result['f1']:.3f}")
    print(f"Markdown: {OUT_MD}")
    print(f"CSV: {OUT_CSV}")
    print(f"Phase report: {PHASE_REPORT}")


if __name__ == "__main__":
    main()
