# routemap_embedding

`routemap_embedding` is the honest descendant of "compact numbers for items": route retrieval through similarity-preserving fingerprints, then rerank the shortlist with full cosine similarity.

This is approximate routing, not exact identity recovery. SimHash signatures, random-projection LSH bands, and product-quantization codes can collide. Distinct items may share a bucket, and relevant items can be false negatives. The benchmark reports recall loss, false-negative rate, latency, and memory so the speed win is kept in view with its cost.

Default vector backend is dependency-free TF-IDF plus numpy. `backend="minilm"` is optional and only used if `sentence_transformers` is importable; otherwise it falls back to TF-IDF.

```powershell
$env:PYTHONPATH = "src"
python -B -m routemap_embedding run --out $env:TEMP\routemap_embedding
```

Outputs:

- real-gold recall@10 against gold target segments
- synthetic-scale recall@10 against brute-force top-k
- false-negative rate
- full-search vs routed-search latency
- vector bytes and fingerprint bytes
