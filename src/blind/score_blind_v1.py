"""Score the FROZEN blind v1 set with the route engines, exactly ONCE.

Verifies the SHA-256 manifest first and refuses to run if any file changed. Ground truth is the
independently-generated labels; the engines never grade themselves. No tuning, no re-running with tweaks.
"""
from __future__ import annotations
import json, csv, hashlib, re
from pathlib import Path

BLIND = Path("data/blind/v1")


def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _jsonl(p): return [json.loads(l) for l in (BLIND / p).read_text().splitlines() if l.strip()]


def verify_frozen():
    man = json.loads((BLIND / "manifest.json").read_text())
    for f, h in man["sha256"].items():
        if _sha(BLIND / f) != h:
            raise SystemExit(f"FROZEN HASH MISMATCH on {f}: the blind set was modified; refusing to score.")
    return man


def score_arithmetic():
    from routemap_digital import verify
    rows = _jsonl("arithmetic_blind_500.jsonl")
    caught = fp = blind_caught = n_resid = n_correct = n_blind = 0
    for r in rows:
        ruled = verify(r["expr_spec"], int(r["claimed_answer"]))["verdict"] == "RULED_OUT_WRONG"
        if r["label"] == "correct":
            n_correct += 1; fp += ruled
        elif r["error_type"] == "residue_inconsistent":
            n_resid += 1; caught += ruled
        else:
            n_blind += 1; blind_caught += ruled
    return {"n": len(rows), "catch_rate_residue_inconsistent": round(caught / max(1, n_resid), 4),
            "false_positive_rate": round(fp / max(1, n_correct), 4),
            "off_by_M_caught_rate": round(blind_caught / max(1, n_blind), 4),
            "n_correct": n_correct, "n_residue_inconsistent": n_resid, "n_off_by_M": n_blind}


def score_schema():
    from routemap_validators import check_output
    rows = _jsonl("schema_outputs_blind_200.jsonl")
    caught = fp = unchk = n_valid = n_violation = 0
    for r in rows:
        v = check_output(r["output"], "json_schema", spec=r["schema"]).verdict
        if r["label"] == "valid":
            n_valid += 1; fp += (v == "RULED_OUT_WRONG")
        else:
            n_violation += 1; caught += (v == "RULED_OUT_WRONG")
        unchk += (v == "UNCHECKABLE")
    return {"n": len(rows), "catch_rate": round(caught / max(1, n_violation), 4),
            "false_positive_rate": round(fp / max(1, n_valid), 4),
            "uncheckable_rate": round(unchk / len(rows), 4), "n_valid": n_valid, "n_violation": n_violation}


def score_extraction():
    rows = list(csv.DictReader((BLIND / "extraction_blind_100.csv").open(encoding="utf-8")))
    def extract(passage, k=6):
        toks = re.findall(r"[A-Za-z][A-Za-z'-]+", passage)
        out = []
        for i, t in enumerate(toks):
            if i > 0 and t[0].isupper() and t not in out:
                out.append(t)
        return out[:k]
    rec = 0.0
    for r in rows:
        gold = [g.strip().lower() for g in r["gold_entities"].split("|") if g.strip()]
        pred = [p.lower() for p in extract(r["passage"])]
        rec += sum(1 for g in gold if g in pred) / max(1, len(gold))
    return {"n": len(rows), "entity_recall": round(rec / max(1, len(rows)), 4),
            "note": "deterministic capitalized-entity baseline (offline); the LLM extractor is ollama-gated"}


def score_retrieval(k=10):
    from routemap_embedding.vectors import build_vectors
    from routemap_embedding.index import EmbeddingRouteIndex
    from routemap_embedding.fingerprints import RandomProjectionLSH
    corpus = _jsonl("retrieval_corpus.jsonl"); queries = _jsonl("retrieval_blind_100.jsonl")
    docs = [{"id": d["id"], "text": d["text"]} for d in corpus]
    combined, _, _ = build_vectors(docs + [{"id": f"q{i}", "text": q["query"]} for i, q in enumerate(queries)], backend="tfidf")
    dmat, qmat = combined[:len(docs)], combined[len(docs):]
    ids = [d["id"] for d in docs]
    full = EmbeddingRouteIndex(dmat, ids, RandomProjectionLSH(seed=7))
    route = EmbeddingRouteIndex(dmat, ids, RandomProjectionLSH(n_planes=16, n_bands=4, seed=7))
    fh = rh = 0
    for q, qv in zip(queries, qmat):
        g = q["gold_doc_id"]
        fh += g in set(full.full_search(qv, k=k))
        rh += g in set(route.route_search(qv, k=k, shortlist_mult=8))
    return {"n": len(queries), f"full_recall_at_{k}": round(fh / len(queries), 4),
            f"route_recall_at_{k}": round(rh / len(queries), 4)}


def main():
    man = verify_frozen()
    print("frozen hashes verified OK\n")
    res = {"seed": man["seed"], "arithmetic": score_arithmetic(), "schema": score_schema(),
           "extraction": score_extraction(), "retrieval": score_retrieval()}
    Path("data/blind/v1/BLIND_RESULTS.json").write_text(json.dumps(res, indent=2, sort_keys=True))
    print(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    main()
