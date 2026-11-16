# ACORD query schema

`ml/eval/acord_eval.py` reads `eval/fixtures/acord_queries.csv`, which is not included here:
it is The Atticus Project's own data, and needs its own download rather than being
vendored into this repository.

## Format

One row per rated (query, clause) pair:

| column | type | meaning |
|---|---|---|
| `query_id` | string | ACORD's query identifier |
| `query_text` | string | the query string |
| `precedent_id` | string | a precedent row's id, as seeded by `pipelines/seed/cuad_precedent.py` |
| `relevance` | int | 0 to 3, ACORD's lawyer-assigned relevance rating |

## Before running the eval

1. Download ACORD from The Atticus Project and map its clause references onto the
   `precedent.id` values this project seeded from CUAD, since the two datasets index
   clauses differently.
2. Seed precedent and let the outbox relay push it into OpenSearch (see the README's
   "Known limits" section for the exact commands).
3. Run `PYTHONPATH=.:libs python3 ml/eval/acord_eval.py` to get the BM25, kNN, hybrid and
   hybrid+rerank comparison table.
