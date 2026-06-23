# Phase 5 Slice 14 - Embedding Fingerprint Retrieval

Date: 2026-06-23

## Purpose

Build `routemap_embedding`, a standalone approximate retrieval package for routing queries through similarity-preserving fingerprints, then reranking the routed shortlist with full cosine similarity.

This is approximate routing, not exact identity recovery. SimHash signatures, random-projection LSH bands, and product-quantization codes can collide. Distinct items can share a bucket, and relevant items can be false negatives. The benchmark reports recall loss and false-negative rate alongside latency and memory.

## Files Added

- `src/routemap_embedding/__init__.py`
- `src/routemap_embedding/__main__.py`
- `src/routemap_embedding/README.md`
- `src/routemap_embedding/bench.py`
- `src/routemap_embedding/fingerprints.py`
- `src/routemap_embedding/index.py`
- `src/routemap_embedding/run_embedding_bench.py`
- `src/routemap_embedding/vectors.py`
- `re_test_embedding.py`

## Fingerprints

- SimHash: seeded random hyperplane signature, exact signature buckets.
- RandomProjectionLSH: seeded hyperplanes split into bands; candidates share at least one band bucket.
- ProductQuantizer: seeded per-subspace codebooks; approximate distances select a shortlist before full cosine rerank.

Default vector backend is TF-IDF with numpy. `backend="minilm"` is optional and only used when `sentence_transformers` is importable; otherwise the package falls back to TF-IDF.

## Real-Gold Recall Sanity

Backend: `tfidf`

Corpus: 109 vectors x 666 dimensions

Scale caveat: only 6 filled QA rows with non-empty `query` and `gold_required_segment_ids` were available, so this is a sanity check rather than a stable product metric.

| Fingerprint | full_recall@10 | route_recall@10 | recall_loss |
| --- | ---: | ---: | ---: |
| SimHash | 0.333 | 0.000 | 0.333 |
| LSH | 0.333 | 0.167 | 0.167 |
| PQ | 0.333 | 0.333 | 0.000 |

Recall is measured against gold target segments, not against fingerprint buckets.

## Synthetic Recall vs Latency

Synthetic index size: 20,000 vectors

Reference: brute-force `full_search` top-10.

Vector memory: 53,280,000 bytes.

| Fingerprint | shortlist_mult | recall@10 | false_negative_rate | full_ms | route_ms | speedup | fingerprint_bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SimHash | 2 | 0.133 | 0.867 | 25.398 | 0.058 | 437.14 | 111968 |
| SimHash | 4 | 0.133 | 0.867 | 25.398 | 0.035 | 721.53 | 111968 |
| SimHash | 8 | 0.133 | 0.867 | 25.398 | 0.034 | 750.30 | 111968 |
| SimHash | 16 | 0.133 | 0.867 | 25.398 | 0.035 | 724.61 | 111968 |
| SimHash | 32 | 0.133 | 0.867 | 25.398 | 0.044 | 581.18 | 111968 |
| LSH | 2 | 0.890 | 0.110 | 26.221 | 20.109 | 1.30 | 703936 |
| LSH | 4 | 0.890 | 0.110 | 26.221 | 21.107 | 1.24 | 703936 |
| LSH | 8 | 0.890 | 0.110 | 26.221 | 20.088 | 1.31 | 703936 |
| LSH | 16 | 0.890 | 0.110 | 26.221 | 20.540 | 1.28 | 703936 |
| LSH | 32 | 0.890 | 0.110 | 26.221 | 21.052 | 1.25 | 703936 |
| PQ | 2 | 0.325 | 0.675 | 26.696 | 0.783 | 34.09 | 162624 |
| PQ | 4 | 0.379 | 0.621 | 26.696 | 0.776 | 34.40 | 162624 |
| PQ | 8 | 0.471 | 0.529 | 26.696 | 0.931 | 28.68 | 162624 |
| PQ | 16 | 0.548 | 0.452 | 26.696 | 1.123 | 23.76 | 162624 |
| PQ | 32 | 0.631 | 0.369 | 26.696 | 2.161 | 12.36 | 162624 |

## Chosen Operating Points

| Fingerprint | shortlist_mult | recall@10 | speedup | minimum_candidate | strong_candidate |
| --- | ---: | ---: | ---: | --- | --- |
| SimHash | 8 | 0.133 | 750.30 | no | no |
| LSH | 8 | 0.890 | 1.31 | no | no |
| PQ | 32 | 0.631 | 12.36 | no | no |

## Bars

| Bar | Result |
| --- | --- |
| minimum_bar | FAIL |
| strong_bar | FAIL |

Minimum bar requires recall@10 > 0.95 at >=2x speed. Strong bar requires recall@10 > 0.98 at >=5x speed. Neither was honestly met.

## Tradeoff Verdict

On this TF-IDF synthetic setup, speed and recall split apart. SimHash and PQ are fast but have large false-negative rates. LSH preserves more of the brute-force top-10, but its buckets are broad enough that the routed path scans much of the index and does not reach 2x speed. A configuration probe confirmed the same shape: high-recall LSH settings can approach 0.98-1.00 recall only by scanning nearly the whole index, while faster LSH settings lose too much recall.

## Verification

```text
python -B -m pytest re_test_embedding.py -q
7 passed

PYTHONPATH=src python -B -m routemap_embedding run --synthetic-n 20000 --out %TEMP%\routemap_embedding_slice14_final
minimum_bar FAIL
strong_bar FAIL
```
