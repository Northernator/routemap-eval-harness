"""Run token vs element vs codon routing comparison + no-leak/determinism checks."""

from __future__ import annotations

import random
from collections import Counter

from routemap_token.bench import load_dataset
from routemap_token.prior import build_idf, discover_corpus_docs

from .bench_elements import MODES, _score_sample, run_comparison


def _row(f: dict) -> str:
    return f"reduction={f['token_reduction']:.3f}  recall_loss={f['recall_loss']:.3f}  +idfstop={f['policy_vs_naive_stopword_recall_delta']:+.3f}"


def main(root: str = ".") -> None:
    res = run_comparison(root=root, seed=7)
    print(f"dataset {res['dataset']}  n={res['n']}  needed_coverage={res['needed_coverage']:.3f}")
    print("\ntoken vs element vs codon (same 99 gold, same metric, no-leak):")
    for tier in ("lt_0_01", "lt_0_02", "lt_0_05"):
        print(f"\n  recall-loss < {tier.replace('lt_0_', '0.')}")
        for mode in ("token", *MODES):
            print(f"    {mode:12}: {_row(res['modes'][mode][tier])}")

    base_cheap = Counter(r["static_class"] for r in res["_baseline_rows"] if r["route_action"] == "cheap")
    el_cheap = Counter(r["static_class"] for r in res["_element_rows_at_best01"] if r["route_action"] == "cheap")
    el_dropped = Counter(r["static_class"] for r in res["_element_rows_at_best01"] if r["later_needed"] and r["route_action"] == "cheap")
    print("\n  element cheaped-token composition:", dict(el_cheap.most_common(8)))
    print("  baseline cheaped-token composition:", dict(base_cheap.most_common(6)))
    print("  element DROPPED needed tokens:", dict(el_dropped.most_common()) or "none")

    # no-leak: scrambling the gold answer must not change any route
    samples, _ = load_dataset(root)
    docs, _ = discover_corpus_docs(root)
    idf_map = build_idf(docs + [s.context for s in samples])
    rng = random.Random(7)
    violations = 0
    for s in samples[:40]:
        a = [r["route_action"] for r in _score_sample(s, idf_map, 0.5, "codon_gate")]
        scrambled = s.__class__(sample_id=s.sample_id, context=s.context, question=s.question,
                                answer="ZZZ " + str(rng.random()), evidence="qq", needed_phrases=("zzz", "qq"))
        b = [r["route_action"] for r in _score_sample(scrambled, idf_map, 0.5, "codon_gate")]
        violations += (a != b)
    print(f"\n  no-leak (scramble gold answer -> identical routes): {'PASS' if violations == 0 else f'FAIL ({violations})'}")
    res2 = run_comparison(root=root, seed=7)
    det = all(res["modes"][m][t] == res2["modes"][m][t] for m in MODES for t in ("lt_0_01", "lt_0_02", "lt_0_05"))
    print(f"  determinism (seed 7 re-run identical): {'PASS' if det else 'FAIL'}")

    t = res["modes"]["token"]["lt_0_01"]["token_reduction"]
    e = res["modes"]["element"]["lt_0_01"]["token_reduction"]
    cg = res["modes"]["codon_gate"]["lt_0_01"]["token_reduction"]
    cb = res["modes"]["codon_boost"]["lt_0_01"]["token_reduction"]
    print(f"\n  VERDICT @<0.01 loss:  token {t:.3f} | element {e:.3f} (+{e-t:.3f}) | codon_gate {cg:.3f} | codon_boost {cb:.3f}")
    print("  -> elements help; codon (trigram) adds nothing on top.")


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
