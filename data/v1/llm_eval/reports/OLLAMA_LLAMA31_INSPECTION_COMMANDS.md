# Ollama llama3.1 Inspection Commands

Run from:

```powershell
Set-Location '<path-to-clone>\routemap-eval-harness'
```

## First 5 Raw Outputs

```powershell
Get-Content data/v1/llm_eval/outputs/ollama_llama31_outputs_full.jsonl -TotalCount 5
```

## Predicted Role Distribution

```powershell
python -c "import csv,collections; c=collections.Counter(r['pred_role'] for r in csv.DictReader(open('data/v1/llm_eval/predictions/ollama_llama31_full_predictions.csv',encoding='utf-8-sig'))); print(c)"
```

## Rows With Empty Entities

```powershell
python -c "import csv; rows=list(csv.DictReader(open('data/v1/llm_eval/predictions/ollama_llama31_full_predictions.csv',encoding='utf-8-sig'))); [print(r['segment_id'], r['gold_entities']) for r in rows if not r['pred_entities'].strip()]"
```

## Rows With Correct Role

```powershell
python -c "import csv; rows=list(csv.DictReader(open('data/v1/llm_eval/predictions/ollama_llama31_full_predictions.csv',encoding='utf-8-sig'))); [print(r['segment_id'], r['gold_role'], r['pred_role']) for r in rows if r['gold_role']==r['pred_role']]"
```

## Rows With Entity Zero Overlap

```powershell
python -c "import csv; rows=list(csv.DictReader(open('data/v1/llm_eval/reports/ollama_llama31_full_evaluation_rows.csv',encoding='utf-8-sig'))); [print(r['segment_id'], r['gold_entities'], '=>', r['pred_entities']) for r in rows if float(r['entity_jaccard'])==0.0]"
```
