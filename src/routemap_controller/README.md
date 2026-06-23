# routemap_controller

`routemap_controller` is the unified RouteMap control loop. It does not add new routing math. It classifies the task, builds the relevant route signature, sends the work to the existing route family, attaches a validator, and escalates whenever no safe guarded cheap path exists.

Every cheap decision is guarded:

- arithmetic uses `routemap_digital.verify`
- JSON and Python code use `routemap_validators.check_output`
- long-context QA uses `routemap_token` token routing with an answer-span recall guard
- retrieval uses `routemap_embedding.EmbeddingRouteIndex` with full cosine rerank guard

High risk and full-budget requests escalate to full compute with validator. Unknown tasks escalate instead of silently pruning.

```powershell
$env:PYTHONPATH = "src"
python -B -m routemap_controller demo
```

Demo outputs:

- `data/v1/digital_route/slice_15_controller/demo_action_plans.md`
- `data/v1/digital_route/slice_15_controller/route_decisions.jsonl`
