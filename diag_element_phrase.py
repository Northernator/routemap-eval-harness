#!/usr/bin/env python3
"""element_phrase headroom diagnostic (v2 — corrected).

v1 bug: "rescuable" counted any dropped answer token with a load-bearing NEIGHBOR,
which over-counts because content words cluster. element_phrase only protects GLUE
(low-weight tokens) inside load-bearing compounds, so the right question is:
how many dropped ANSWER tokens are themselves glue?  (v1 also ran route_passage at
its default operating point, which prunes far harder than the validated element tier.)

v2 fixes both:
  - ranks tokens by the router's real per-token route_score and sweeps the KEEP
    fraction, so we read recall at the validated tier (~0.44 reduction = keep ~56%),
    not just route_passage's aggressive default.
  - splits answer-token losses into GLUE losses (what element_phrase could fix) vs
    CONTENT losses (what it cannot).

Run from repo root:  python diag_element_phrase.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from routemap_token import bench
from routemap_token.elements import classify_element, ELEMENT_WEIGHT
from routemap_token.routers import route_passage

GLUE = {e for e, w in ELEMENT_WEIGHT.items() if w < 0.40}          # FUNCTION, CONNECTOR, ...
LOAD_BEARING = {e for e, w in ELEMENT_WEIGHT.items() if w >= 0.60}

samples, name = bench.load_dataset(ROOT)
print(f"dataset: {name} | samples: {len(samples)}")
print(f"glue elements (w<0.40): {sorted(GLUE)}\n")

# Pre-extract per-sample: token elements, route_scores, needed mask.
rows = []
skipped = 0
for s in samples:
    toks = bench.tokenize_with_spans(s.context)
    routed = route_passage(s.context, s.question, router_mode="element")
    if len(routed) != len(toks):
        skipped += 1
        continue
    need = set(bench.needed_token_indices(s)[0])
    el = [classify_element(t) for t, _, _ in toks]
    scores = [r["route_score"] for r in routed]
    rows.append((el, scores, need))

def evaluate(keep_frac: float):
    """Keep the top `keep_frac` of tokens per sample by route_score; measure recall + loss types."""
    needed = kept_needed = glue_loss = content_loss = glue_in_compound = 0
    for el, scores, need in rows:
        n = len(el)
        k = max(1, round(keep_frac * n))
        keepset = set(sorted(range(n), key=lambda i: -scores[i])[:k])
        for i in need:
            needed += 1
            if i in keepset:
                kept_needed += 1
            elif el[i] in GLUE:
                glue_loss += 1
                nb = (el[i - 1] if i else None, el[i + 1] if i + 1 < n else None)
                if any(x in LOAD_BEARING for x in nb):
                    glue_in_compound += 1
            else:
                content_loss += 1
    recall = kept_needed / max(1, needed)
    return recall, glue_loss, content_loss, glue_in_compound, needed

print(f"samples used: {len(rows)} (skipped {skipped})")
print(f"{'reduction':>9} {'keep':>5} {'recall':>7} {'loss':>6} | {'GLUE_loss':>9} {'CONTENT_loss':>12} {'glue_in_cmpd':>12}")
results = {}
for keep_frac in (0.70, 0.56, 0.44):          # reductions 0.30, 0.44, 0.56
    rec, gl, cl, gic, nd = evaluate(keep_frac)
    results[keep_frac] = (rec, gl, cl, gic)
    print(f"{1-keep_frac:>9.2f} {keep_frac:>5.2f} {rec:>7.3f} {1-rec:>6.3f} | {gl:>9} {cl:>12} {gic:>12}")

# Verdict at the validated tier (keep 0.56 ~ reduction 0.44).
rec, gl, cl, gic = results[0.56]
print("\nAt the validated element tier (~0.44 reduction):")
print(f"   needed-token recall = {rec:.3f}  (loss {1-rec:.3f})")
print(f"   answer-token losses that are GLUE (element_phrase target) = {gl}")
print(f"   answer-token losses that are CONTENT (element_phrase cannot fix) = {cl}")
print("\nVERDICT:", end=" ")
if gl == 0 or gl < cl * 0.25:
    print("element_phrase is a CLEAN NEGATIVE on this set -- the recall losses are\n"
          "         CONTENT tokens (CONCEPT/SYSTEM/ACTION), not glue. Phrase protection\n"
          "         recovers ~nothing. If you want more recall, raise CONTENT-element\n"
          "         retention (weights/budget), not codons.")
else:
    print(f"element_phrase has real glue headroom ({gl} glue losses vs {cl} content).\n"
          "         Build it PROTECT-ONLY and confirm on the frozen blind gate.")

# ---------------------------------------------------------------------------
# CODON-FIRST test: does removing glue FIRST, then giving the whole budget to
# content, let the element layer keep more needed CONCEPT/SYSTEM tokens?
# Idealized UPPER BOUND of "codon runs first, leaves residue": glue removal is
# free and every freed slot is reallocated to the best content. Any real
# residue/re-scoring scheme can only do <= this.
# ---------------------------------------------------------------------------
def evaluate_codonfirst(keep_frac: float):
    needed = base_kept = cf_kept = glue_in_kept = 0
    for el, scores, need in rows:
        n = len(el)
        K = max(1, round(keep_frac * n))
        order = sorted(range(n), key=lambda i: -scores[i])
        keep_base = set(order[:K])                          # element as-is
        nonglue_order = [i for i in order if el[i] not in GLUE]
        keep_cf = set(nonglue_order[:K])                    # codon-first: budget -> content only
        glue_in_kept += sum(1 for i in keep_base if el[i] in GLUE)
        for i in need:
            needed += 1
            base_kept += i in keep_base
            cf_kept += i in keep_cf
    return base_kept / max(1, needed), cf_kept / max(1, needed), glue_in_kept

print("\n=== CODON-FIRST reordering (idealized upper bound) ===")
print(f"{'reduction':>9} {'base_recall':>11} {'codonfirst':>11} {'delta':>7} {'glue_slots_freed':>17}")
cf_delta_044 = 0.0
for keep_frac in (0.70, 0.56, 0.44):
    base_r, cf_r, gik = evaluate_codonfirst(keep_frac)
    if abs(keep_frac - 0.56) < 1e-9:
        cf_delta_044 = cf_r - base_r
    print(f"{1-keep_frac:>9.2f} {base_r:>11.3f} {cf_r:>11.3f} {cf_r-base_r:>+7.3f} {gik:>17}")

print("\nCODON-FIRST VERDICT:", end=" ")
if cf_delta_044 < 0.01:
    print(f"NO -- at the validated tier reordering buys {cf_delta_044:+.3f} recall.\n"
          "         Dropped content loses to OTHER content, not to glue; freeing the\n"
          "         ~1% glue slots doesn't land on needed tokens. Pipeline order can't\n"
          "         fix a content-vs-content budget problem.")
else:
    print(f"MAYBE -- reordering buys {cf_delta_044:+.3f} recall at the validated tier.\n"
          "         Worth a real codon-first prototype + blind-gate confirmation.")
