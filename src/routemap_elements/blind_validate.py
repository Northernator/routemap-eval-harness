"""Blind / out-of-domain validation gate for the element router (frozen weights).

Runs token vs element vs codon-gate on the FROZEN external blind set
(data/blind/v1/extraction_blind_100.csv, seed 20260623, never tuned against — a
fresh invented distribution, out-of-domain vs the AI-governance dev gold), reusing
the exact TokenRouteQA recall/reduction frontier. Element weights are frozen; the
printed sha256 makes any post-hoc tuning detectable.

Gate (Chris's criterion): if element beats token at the same (or lower) recall loss
on this out-of-domain blind set, the element router is promote-eligible.

  PYTHONPATH=src python -m routemap_elements.blind_validate
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from routemap_token.bench import (TokenQASample, _frontier_by_tier, _metrics, THRESHOLDS,
                                  needed_span_coverage, score_sample as token_score)
from routemap_token.prior import build_idf

from .bench_elements import CODON_LOADBEARING_FLOOR, _score_sample
from .elements import ELEMENT_WEIGHT

BLIND_CSV = "data/blind/v1/extraction_blind_100.csv"


def frozen_config_hash() -> str:
    frozen = {"ELEMENT_WEIGHT": ELEMENT_WEIGHT,
              "score_coeffs": {"base": 0.55, "idf": 0.25, "qov": 0.30},
              "codon_floor": CODON_LOADBEARING_FLOOR}
    return hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()[:16]


def load_blind(root: str = ".") -> list[TokenQASample]:
    path = Path(root) / BLIND_CSV
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    samples = []
    for r in rows:
        ents = [e.strip() for e in (r.get("gold_entities") or "").split("|") if e.strip()]
        ans = (r.get("gold_answer") or "").strip()
        needed = tuple(dict.fromkeys(ents + ([ans] if ans else [])))
        samples.append(TokenQASample(sample_id=r["id"], context=r["passage"],
                       question=(r.get("question") or "").strip(), answer=ans,
                       evidence="; ".join(ents), needed_phrases=needed))
    return samples


def _frontier(samples, idf, mode):
    curve, rbt = [], {}
    for c in THRESHOLDS:
        if mode == "token":
            rows = [r for s in samples for r in token_score(s, idf, c)]
        else:
            rows = [r for s in samples for r in _score_sample(s, idf, c, mode)]
        rbt[c] = rows
        curve.append({"threshold": c, **_metrics(rows)})
    return _frontier_by_tier(curve, rbt, seed=7)


def run(root: str = ".") -> dict:
    samples = load_blind(root)
    cov = needed_span_coverage(samples)
    idf = build_idf([s.context for s in samples])
    res = {m: _frontier(samples, idf, m) for m in ("token", "element", "codon_gate")}
    t = res["token"]["lt_0_01"]
    e = res["element"]["lt_0_01"]
    gate = e["token_reduction"] > t["token_reduction"] + 0.01 and e["recall_loss"] <= t["recall_loss"] + 0.005
    return {"frozen_hash": frozen_config_hash(), "n": len(samples), "coverage": cov["coverage"],
            "token": t, "element": e, "codon_gate": res["codon_gate"]["lt_0_01"],
            "delta": e["token_reduction"] - t["token_reduction"], "gate_pass": gate}


def main(root: str = ".") -> int:
    r = run(root)
    print(f"frozen element config sha256[:16] = {r['frozen_hash']}")
    print(f"blind set: N={r['n']}  needed_coverage={r['coverage']:.3f}  (OOD, never tuned)")
    print(f"  token      : reduction {r['token']['token_reduction']:.3f}  recall_loss {r['token']['recall_loss']:.3f}")
    print(f"  element    : reduction {r['element']['token_reduction']:.3f}  recall_loss {r['element']['recall_loss']:.3f}")
    print(f"  codon_gate : reduction {r['codon_gate']['token_reduction']:.3f}  recall_loss {r['codon_gate']['recall_loss']:.3f}")
    print(f"  delta (element-token): {r['delta']:+.3f}")
    print("GATE:", "PASS — element promote-eligible" if r["gate_pass"] else "FAIL — keep element experimental")
    return 0 if r["gate_pass"] else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
