# KV-Cache Importance Routing (routemap_matrix)

Model: `auto` on `cuda` | prompt_len 1408

Memory + needle accuracy are the result; tokens/sec is INDICATIVE only (no FlashAttention on Maxwell). `dense` is the correctness anchor.

| policy | budget | needle_hit | peak_VRAM_MB | final_cache_len | guard_triggers | false_prunes |
| --- | ---: | :---: | ---: | ---: | ---: | ---: |
| dense | 1408 | Y | 5478.6 | 1419 | 0 | 0 |
| recency_window | 64 | n | 5478.6 | 64 | 1 | 1 |
| recency_window | 128 | n | 5478.6 | 128 | 1 | 2 |
| recency_window | 256 | n | 5478.6 | 256 | 1 | 1 |
| h2o | 64 | n | 5478.6 | 64 | 0 | 0 |
| h2o | 128 | n | 5478.6 | 128 | 0 | 0 |
| h2o | 256 | n | 5478.6 | 256 | 0 | 0 |
| routemap | 64 | n | 5478.6 | 64 | 1 | 0 |
| routemap | 128 | n | 5478.6 | 128 | 0 | 0 |
| routemap | 256 | n | 5478.6 | 256 | 0 | 0 |