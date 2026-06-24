# Slice 20 — Semantic-element + DNA-codon token routing (element WIN, codon NEGATIVE)

Date: 2026-06-23
Purpose: test Chris's "periodic table of language elements" + "DNA codon" idea — does a richer
functional ELEMENT tagset, and 3-token CODON context, route better than routemap_token's per-token
class prior? Specifically, can context-gating the blanket negation/number/entity force-keep push past
the Slice 13 strong-bar cap?

Code: `src/routemap_elements/` (elements.py = ~33-element deterministic tagger + codon motif scorer;
bench_elements.py reuses routemap_token's exact tokenizer / gold loader / needed-span labels / frontier
/ baselines — only the routing signal changes; run_compare.py; rt_test_elements.py). Offline,
deterministic, no model. Built + verified by Claude in a clean tree (mount served stale/null-byte copies
of edited files; live repo files are authoritative).

## Setup
- Same 99 gold segments, same TokenRouteQA recall/reduction frontier, same random + IDF-stopword
  baselines as routemap_token (imported, not reimplemented) → apples-to-apples, no-leak.
- Modes: `token` (baseline) · `element` (richer per-token tagset) · `codon_gate` (element scoring +
  codon-gated force-keep — the faithful "context-gate the force-keep" hypothesis) · `codon_boost`
  (element + codon-value score boost).
- Element weights + score coefficients set a priori (NOT tuned on this test set; first run gave the headline).

## Result (reduction @ recall-loss < 0.01)
| Mode | Reduction | Recall loss | vs IDF-stopword |
| --- | ---: | ---: | ---: |
| token (baseline) | 0.343 | 0.005 | +0.617 |
| **element** | **0.437** | 0.005 | +0.787 |
| codon_gate | 0.437 | 0.005 | +0.787 |
| codon_boost | 0.410 | 0.005 | +0.721 |

Recall preserved (182/183 needed tokens kept; 1 CONCEPT dropped — same as baseline). no-leak PASS
(scrambling the gold answer leaves every route identical), determinism PASS (seed 7), pytest 5/5.

## Reading
- **Element WIN: 0.343 → 0.437 reduction (+0.094, +27% relative) at the same <1% recall loss**, with a
  bigger margin over the IDF-stopword baseline (+0.79 vs the token prior's +0.62). The richer functional
  tagset cheap-routes ~250 more tokens the per-token prior over-kept (function words, connectors,
  low-value concepts/actions, examples, sequence markers) without dropping answer spans. A real,
  foldable improvement to routemap_token's token lane.
- **Codon (DNA) layer adds NOTHING.** As a force-keep gate it is *identical* to element (0.437): 0/24
  negations were droppable because they all sit in load-bearing local contexts anyway, so the gate
  changed nothing. As a score boost it is *worse* (0.410) — the trigram boost over-protects content
  tokens. Flat across codon floors 0.5–0.7. The trigram context is redundant with per-element weight +
  IDF + question-overlap.
- Strong bar (0.50–0.70 @ <1%) still FAILS (0.437 < 0.50), but element closes ~40% of the gap from the
  baseline.

## Conclusion
The "periodic table of elements" half of the idea is a genuine, measured improvement; the "DNA codon"
half is a clean negative — trigram context adds no routing signal here. Honest framing: mechanically
this is coarse functional-class tagging + (failed) n-gram features — known NLP; the contribution is the
integration and the rigorous no-leak comparison against a real baseline. Caveats: in-domain
AI-governance gold, 99 segments, element weights hand-set a priori (blind-set + fitted-weights
validation = future work). Recommendation: fold the element tagset into routemap_token to lift its
frontier 0.343 → ~0.44; drop the codon layer.

Reproduce: `PYTHONPATH=src python -m routemap_elements.run_compare .` and
`PYTHONPATH=src pytest rt_test_elements.py`.

## Ablation & robustness (added after review)
Falsification — does the element table beat a *simple* heuristic, not just the old prior?
| router | reduction @<1% loss |
| --- | ---: |
| token baseline | 0.343 |
| token + cheap 4 discourse classes (connector/example/sequence/exception) | 0.363 |
| **full element table (33)** | **0.437** |

The simple 4-class heuristic captures only +0.020; the full table earns +0.094 → the
richness is doing real work, not a couple of cheap tricks.

Leave-one-family-out (force-keep a family back; drop = its contribution to the element total):
BOUNDARY −0.250, FUNCTION −0.111, CONNECTOR −0.037, EXAMPLE/SEQ/EXC −0.019, ACTION −0.009,
CONCEPT −0.000. Honest caveat: punctuation/function dominate the *absolute* reduction but are
shared with the baseline; the element table's *advantage over token* is concentrated in
connectors + discourse markers + actions + reorganised scoring.

Split-half (weights are a-priori, not fit): element beats token on BOTH halves —
A: 0.343→0.413 (+0.069), B: 0.342→0.438 (+0.096). Advantage replicates; still in-domain, so a
true out-of-domain/blind segment run is the remaining gate before shipping element as default.

The one dropped needed token: `routemap` (CONCEPT, idf 2.52) — a *rare lowercase domain term* that
is answer-bearing. Systematic risk: the element router can drop a rare content word that isn't
query-overlap. Same "the answers are content/entity words" tension as the rest of the token lane.

Scope correction: the codon-negative is scoped to THIS 99-row in-domain governance benchmark — not a
universal claim. Codons may still matter on longer / nested-clause / order-sensitive / contradiction-
heavy text. Not pursued now; not declared universally dead.

## Router flag (A) + frozen-weight blind gate (B)
**A — `--router` in routemap_token (default unchanged).** `run_benchmark` gained a `router` param
(default `"token"` = byte-identical baseline; 15/15 tests pass, default reduction still 0.343). CLI:
`python -m routemap_token run --router token|element|codon-gate|all`. element/codon-gate are
lazy-imported, so token mode keeps zero dependency on the experimental package. **The default was NOT
changed.** `--router all` on the dev gold: token 0.343 | element 0.437 | codon-gate 0.437.

**B — blind validation gate (frozen weights).** Element config frozen at
`sha256 c7f0cf9e68d763dc` (33 elements + score coeffs 0.55/0.25/0.30 + codon floor 0.60). Ran token vs
element vs codon-gate on the frozen external **out-of-domain** blind set
(`data/blind/v1/extraction_blind_100.csv`, N=100, coverage 1.000, seed 20260623, never tuned):

| router | reduction @<1% loss | recall loss |
| --- | ---: | ---: |
| token | 0.571 | 0.000 |
| **element** | **0.640** | 0.000 |
| codon_gate | 0.633 | 0.000 |

**GATE PASS:** element beats token by **+0.069 at zero recall loss on fresh out-of-domain data with
frozen weights** — the advantage replicates (in-domain +0.094, split-half +0.069/+0.096, OOD +0.069).
Element is **promote-eligible**. Reproduce: `python -m routemap_elements.blind_validate`. Caveat: the
blind set is synthetic (one fresh distribution); recommend keeping `token` the default until one
human/real-doc confirmation before flipping the shipped default.

## Real-document gate + promotion
Per Chris's criterion ("promote only if element still beats token at zero recall loss on a real/human-reviewed
set"), ran the frozen element (same hash c7f0cf9e68d763dc) on two **real** held-out sets:

| real set | token red | element red | recall loss | gate |
| --- | ---: | ---: | ---: | --- |
| natural_language_blind (99 real held-out docs) | 0.290 | 0.386 (+0.096) | 0.005 = 0.005 | PASS |
| heldout adjudicated (80, **human-reviewed**) | 0.251 | 0.296 (+0.045) | 0.000 = 0.000 | PASS |

The element advantage now replicates **five** ways at ≤ token recall loss: in-domain +0.094, split-half
+0.069/+0.096, synthetic-blind +0.069, real natural held-out +0.096, human-adjudicated +0.045.

**PROMOTED: `element` is now the default router.** `run_benchmark` and the CLI default to `element`; the
`token` baseline is preserved and selectable via `--router token` (still 0.343, still tested). Card header
labels the active router; element rows now carry `route_score`+`context_features` so traces work; added
`test_default_router_is_element_and_token_preserved`; fixed `run_comparison` to request `router="token"`
for its baseline. 16/16 token+element tests pass. (Architecture report §4.4 prose still cites the token-lane
34% headline — refresh to "default element ~44%, token baseline 34%".)

## Code/report consistency pass — element FOLDED into routemap_token + default confirmed
Per Chris's spec: (1) **Folded** the element router INTO routemap_token — new `routemap_token/elements.py`
(tagger) + `routers.py` (scorers, `route_passage`, `score_for_mode`, `run_comparison`). `run_benchmark`
param renamed `router`→`router_mode`; `_make_score_fn` now uses `.routers` (token mode keeps zero
dependency on the experimental package; element/codon lazy-imported from within the same package).
`routemap_elements/{elements,bench_elements}.py` reduced to thin re-export shims (blind_validate,
run_compare, rt_test_elements unchanged and still pass). (2) **Default `router_mode="element"`** —
judged comfortable: it passed the pre-registered real-document gate on two human-reviewed sets at 0 recall
loss; recall-preserving and reversible. `token` preserved via `--router token`. Honest scope caveat: the
real confirmation sets were governance-adjacent; the only genuinely-different-domain set was synthetic.
(3) `routemap_controller.route_decide` gains a `router_mode` passthrough; `_long_context_qa` now calls
`routemap_token.route_passage` (default element); engine label unchanged. (4) `run_evidence.py` adds an
element pytest step + `--router all` bench + the frozen blind-gate step. (5) README + EVIDENCE_PACK +
report all state default element ~0.44 / token baseline ~0.34.

Verified in a clean git tree: **pytest rt_test_token + rt_test_elements + rc_test_controller = 25/25**;
`--router all` → token 0.343 / element 0.437 (default) / codon-gate 0.437; frozen blind gate PASS +0.069
(config hash c7f0cf9e unchanged); controller default=element and `router_mode="token"` override both work
with invariants intact; 0 whitespace/conflict issues; routemap_token self-contained; routemap_elements →
routemap_token (correct dependency direction). To run on the live machine: `git diff --check` and the full
`python run_evidence.py` (the sandbox git can't read the Windows index, and run_evidence needs the full
data tree + is ollama/torch-gated).
