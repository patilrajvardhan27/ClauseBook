# Clausebook eval report

## Extraction (illustrative fixture)
- rows: 3
- non-empty extraction rate: 1.00
- gate (exact_match_min): 0.6

## Not run in this environment
- Classification (needs a trained model; see ml/classify/train.py)
- Retrieval (needs OpenSearch populated by pipelines/gold + the outbox relay)
- Placement on the real 150 gold clauses (needs eval/fixtures/gold_clauses.csv, see its schema doc)
- Cost and latency (needs a running API/worker stack)
