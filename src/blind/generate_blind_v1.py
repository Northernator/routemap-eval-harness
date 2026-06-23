"""Generate the RouteMap v1 FROZEN BLIND benchmark.

Discipline: ground truth is computed by independent pure-Python code (never the route engines);
distribution is fresh; seed is fixed (20260623, distinct from the dev seed 7). Run ONCE, freeze with
SHA-256, never tune against it. Re-running with the same seed reproduces byte-identical files.
"""
from __future__ import annotations
import json, csv, math, random, hashlib
from pathlib import Path

SEED = 20260623
OUT = Path("data/blind/v1")
M = 7 * 9 * 11 * 13 * 37 * 101  # combined modulus of the default residue bank


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def gen_arithmetic(rng, n=500):
    fams = ["power", "factorial", "fibonacci", "bigsum", "bigprod"]
    rows = []
    for i in range(n):
        fam = rng.choice(fams)
        if fam == "power":
            b, e = rng.randint(2, 40), rng.randint(40, 400)
            spec, true, prompt = {"family": "power", "base": b, "exponent": e}, pow(b, e), f"{b}^{e}"
        elif fam == "factorial":
            k = rng.randint(10, 80)
            spec, true, prompt = {"family": "factorial", "n": k}, math.factorial(k), f"{k}!"
        elif fam == "fibonacci":
            k = rng.randint(50, 500)
            spec, true, prompt = {"family": "fibonacci", "n": k}, fib(k), f"fib({k})"
        elif fam == "bigsum":
            vals = [rng.randint(1, 10**9) for _ in range(rng.randint(3, 8))]
            spec, true, prompt = {"family": "bigsum", "values": vals}, sum(vals), "+".join(map(str, vals))
        else:
            vals = [rng.randint(2, 10**4) for _ in range(rng.randint(3, 6))]
            spec, true, prompt = {"family": "bigprod", "values": vals}, math.prod(vals), "*".join(map(str, vals))
        r = rng.random()
        if r < 0.5:
            claimed, label, etype = true, "correct", None
        elif r < 0.85:
            off = rng.randint(1, 9999)
            if off % M == 0:
                off += 1
            claimed, label, etype = true + off, "wrong", "residue_inconsistent"
        else:
            claimed, label, etype = true + M * rng.randint(1, 5), "wrong", "off_by_M"
        rows.append({"id": f"arith_{i:04d}", "family": fam, "expr_spec": spec, "prompt": f"{prompt} = ?",
                     "claimed_answer": claimed, "label": label, "error_type": etype})
    return rows


def gen_schema(rng, n=200):
    fields = ["score", "rating", "count", "level", "priority", "rank", "amount", "weight"]
    rows = []
    for i in range(n):
        f = rng.choice(fields)
        lo, hi = 0, rng.choice([5, 10, 100, 1000])
        req = rng.choice(["label", "name", "title", "key"])
        schema = {"type": "object", "required": [f, req],
                  "properties": {f: {"type": "integer", "minimum": lo, "maximum": hi},
                                 req: {"type": "string"}}}
        good_val = rng.randint(lo, hi)
        good = {f: good_val, req: rng.choice(["alpha", "beta", "gamma", "delta"])}
        r = rng.random()
        if r < 0.5:
            obj, label, vtype = good, "valid", None
        elif r < 0.7:
            obj, label, vtype = {**good, f: hi + rng.randint(1, 50)}, "violation", "above_maximum"
        elif r < 0.82:
            obj, label, vtype = {**good, f: lo - rng.randint(1, 50)}, "violation", "below_minimum"
        elif r < 0.92:
            obj = dict(good); del obj[req]; label, vtype = "violation", "missing_required"
        else:
            obj, label, vtype = {**good, f: f"{good_val}"}, "violation", "wrong_type"
        body = json.dumps(obj)
        # ~40% wrapped in markdown / prose to exercise the extraction boundary
        w = rng.random()
        if w < 0.25:
            raw = f"```json\n{body}\n```"
        elif w < 0.4:
            raw = f"Here is the JSON:\n{body}"
        else:
            raw = body
        rows.append({"id": f"schema_{i:04d}", "schema": schema, "output": raw, "label": label, "violation_type": vtype})
    return rows


ENTS = ["Vextan", "Mirelle", "Korrowind", "Sabreth", "Quillon", "Dravaile", "Thornby", "Eskelund",
        "Pravich", "Wendaloo", "Crestfall", "Brimhollow", "Ashvane", "Lurewick", "Galmont"]
TERMS = ["protocol", "ledger", "turbine", "manifest", "estuary", "alloy", "cipher", "quorum",
         "lattice", "beacon", "rampart", "syndicate", "reservoir", "almanac", "foundry"]


def gen_extraction(rng, n=100):
    rows = []
    for i in range(n):
        e1, e2 = rng.sample(ENTS, 2)
        t1, t2 = rng.sample(TERMS, 2)
        passage = (f"In the {t1} review, {e1} approved the {t2} for {e2} without amendment. "
                   f"The {t2} remains in force pending the next {t1} cycle.")
        gold = [e1, e2, t2]
        question = f"Who approved the {t2}?"
        rows.append({"id": f"extract_{i:04d}", "passage": passage, "gold_entities": "|".join(gold),
                     "question": question, "gold_answer": e1})
    return rows


def gen_retrieval(rng, n=100):
    # fresh corpus: one distinct doc per query (known-answer retrieval)
    corpus, queries = [], []
    for i in range(n):
        topic = rng.choice(TERMS) + "-" + rng.choice(ENTS).lower()
        secret = f"{rng.choice(ENTS)}-{rng.randint(100,999)}"
        text = (f"The {topic} dossier records that the responsible custodian is {secret}. "
                f"All {topic} entries are reconciled quarterly by the oversight board.")
        did = f"doc_{i:04d}"
        corpus.append({"id": did, "text": text})
        queries.append({"id": f"ret_{i:04d}", "query": f"Who is the responsible custodian for the {topic} dossier?",
                        "gold_doc_id": did})
    # add distractor docs so retrieval is non-trivial
    for j in range(n):
        t = rng.choice(TERMS); e = rng.choice(ENTS)
        corpus.append({"id": f"distractor_{j:04d}", "text": f"The {t} archive notes routine maintenance by {e} with no exceptions logged."})
    rng.shuffle(corpus)
    return {"corpus": corpus, "queries": queries}


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as h:
        for r in rows:
            h.write(json.dumps(r, sort_keys=True) + "\n")


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    arith = gen_arithmetic(rng)
    schema = gen_schema(rng)
    extraction = gen_extraction(rng)
    retrieval = gen_retrieval(rng)
    write_jsonl(OUT / "arithmetic_blind_500.jsonl", arith)
    write_jsonl(OUT / "schema_outputs_blind_200.jsonl", schema)
    write_csv(OUT / "extraction_blind_100.csv", extraction)
    write_jsonl(OUT / "retrieval_blind_100.jsonl", retrieval["queries"])
    write_jsonl(OUT / "retrieval_corpus.jsonl", retrieval["corpus"])
    files = ["arithmetic_blind_500.jsonl", "schema_outputs_blind_200.jsonl",
             "extraction_blind_100.csv", "retrieval_blind_100.jsonl", "retrieval_corpus.jsonl"]
    manifest = {"name": "routemap_blind_v1", "seed": SEED, "generator": "generate_blind_v1.py",
                "discipline": "independent ground truth; run once; frozen; never tuned against",
                "counts": {"arithmetic": len(arith), "schema": len(schema),
                           "extraction": len(extraction), "retrieval_queries": len(retrieval["queries"]),
                           "retrieval_corpus": len(retrieval["corpus"])},
                "sha256": {f: sha256(OUT / f) for f in files}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print("FROZEN blind v1:")
    for f in files:
        print(f"  {f}: {sha256(OUT/f)[:16]}...")
    print("counts:", manifest["counts"])


if __name__ == "__main__":
    main()
