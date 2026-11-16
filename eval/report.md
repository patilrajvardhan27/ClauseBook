# Clausebook eval report
- generated: 2026-11-16T14:57:48.571926+00:00
- commit: cc09cb6
- gold data version: no eval/fixtures/gold_clauses.csv yet

## Extraction (illustrative fixture)
- rows: 3
- non-empty extraction rate: 1.00
- gate (exact_match_min): 0.6

## Classification
Not run: data/gold/segments.csv missing. Run pipelines/gold/run_gold.py first.

## Retrieval (ACORD)
Not run: eval/fixtures/acord_queries.csv missing. See its schema doc.

## Placement
Not run: eval/fixtures/gold_clauses.csv missing. See its schema doc.

## Cost and latency
Not run: needs the Docker Compose stack up and 20+ contracts fed through it. See ml/eval/perf.py.
