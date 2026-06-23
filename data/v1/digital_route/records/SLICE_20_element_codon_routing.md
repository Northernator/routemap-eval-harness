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
