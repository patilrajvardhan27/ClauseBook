# Clausebook

Contract review that knows a firm's playbook. Clausebook reads a counterparty draft, finds each
clause, places it against the firm's ordered positions (preferred, fallbacks, walk-away), and
proposes the right fallback as a minimal tracked change in Word, with the precedent it came from.

Not affiliated with or endorsed by any commercial contract-review product.

## The problem

A partner says "our fallbacks never come out right." Underneath that sentence are four separate
failures, and each one is a design requirement, not a bug to patch later.

![Four failures behind a bad fallback, and Clausebook's answer to each](docs/images/problem-solution.svg)

Short version: fallback selection is a ranking problem over an ordered set with conditions, not a
retrieval problem. Retrieval only supplies evidence (a precedent clause that shows a position has
been accepted before). The decision of *which* position to propose comes from the firm's ladder
order and a handful of per-attribute rules.

## The solution

1. **Segment** the document into clause-sized spans, numbered-heading first, sentence-boundary as
   a fallback for contracts with no numbering at all.
2. **Classify** each segment's clause type on its text, not its heading. A clause can carry more
   than one category, and headings lie, so this is a multi-label model.
3. **Extract** the deal terms that actually matter (cap multiple, notice days, carve-outs) with
   deterministic rules first; a schema-validated model fills only what rules miss.
4. **Place** the clause on the firm's ordered ladder: find where it sits today, then find the best
   position ahead of that which the counterparty hasn't already rejected in this negotiation.
5. **Redline** the clause as a word-level minimal diff from the counterparty's text to the
   approved language: insert/delete hunks, never a block replacement.

![The placement algorithm's decision flow](docs/images/placement-flow.svg)

Every decision carries its evidence (the extracted attributes, the retrieved precedent, and the
rule that fired), stored on the finding, not re-derived after the fact, so a lawyer can always see
why a fallback was proposed.

## System architecture

![Clausebook system architecture: add-in and web app over a FastAPI service, a Postgres-backed
job queue driving a worker pipeline, and a derived OpenSearch precedent index](docs/images/architecture.svg)

Six decisions, each recorded as an ADR in [`docs/adr/`](docs/adr/):

1. **[Postgres job queue](docs/adr/0001-postgres-job-queue.md)** instead of a broker: a job and
   its review commit in one transaction.
2. **[Outbox to OpenSearch](docs/adr/0002-outbox-to-opensearch.md)**: Postgres stays the source of
   truth; the search index is derived and rebuildable.
3. **[Rules before models](docs/adr/0003-rules-before-models.md)**: deterministic extraction and
   placement run first; a model only fills what rules can't reach.
4. **[Streaming findings](docs/adr/0004-streaming-findings.md)**: SSE events per clause, so the
   first finding on a 100-page contract arrives in seconds, not minutes.
5. **[Row-level security](docs/adr/0005-row-level-security.md)**: tenant isolation enforced in
   Postgres, not only in application code.
6. **[No customer data in training](docs/adr/0006-no-customer-data-in-training.md)**: a firm's
   documents feed only that firm's own precedent index.

## Repository layout

```
clausebook/
  apps/web, apps/addin        React + TS front ends (web app, Word task pane)
  packages/ui, api-client     shared components and a typed fetch/SSE client
  services/api                FastAPI: routers, domain, SSE
  services/worker              Postgres-queue worker: one stage per file
  libs/clausebook_core        shared Python: ontology models, the placement engine, diff, config
  pipelines/                  bronze -> silver -> gold for CUAD; sample-playbook seed
  ml/                         classify, extract, retrieve, eval
  eval/                       thresholds.yaml, fixtures, report.md
  db/migrations                Alembic
  deploy/                      docker-compose, Dockerfiles, OTel collector
  docs/                        ADRs, images, data sources
```

One placement engine, imported by both the API (preview) and the worker (full review), never a
second copy. Every source file stays under 250 lines by design; `scripts/check-file-length.mjs`
enforces it in CI.

## Running it

```bash
cd deploy && docker compose up    # Postgres, OpenSearch, API, worker, web app, OTel collector
cd db/migrations && alembic upgrade head
PYTHONPATH=.:libs python3 pipelines/seed/run_seed.py   # eight sample clause-type ladders
```

The API comes up on `:8000`, the web app on `:5173`. The Word add-in (`apps/addin`) sideloads
against a Microsoft 365 developer tenant; see its manifest at `apps/addin/manifest.xml`.

Run the parts that need no live infrastructure directly:

```bash
source .venv/bin/activate   # or create one: python3 -m venv .venv
pip install -e ".[dev]"
PYTHONPATH=.:libs pytest tests/ -q          # unit tests: the placement engine, extractors
PYTHONPATH=.:libs python3 ml/eval/cli.py    # writes eval/report.md
node scripts/check-file-length.mjs
```

## Known limits

Verified against a real Postgres 16 container: the migration applies cleanly, the eight sample
playbooks seed correctly, and a pasted clause through `POST /v1/playbooks/{id}/preview` is
extracted, laddered, and gets back the right fallback with a plain-language reason.

What's genuinely exercised:
- The ontology (15 tables), migrated and queried against live Postgres.
- The placement engine (`libs/clausebook_core/placement`), unit-tested and run through the API
  and the worker's `place` stage.
- Deterministic term extraction for all eight v1 clause types, exact-match tested.
- The minimal-diff redline builder, producing true word-level hunks, not block replacement.
- The full FastAPI surface (12 endpoints) and the worker's seven-stage pipeline, import- and
  type-checked end to end.
- The web app and the Word add-in, both building clean under `tsc`.

What's still open, and why:
- **Classification** runs a TF-IDF baseline trained on a dozen hand-written sentences
  (`ml/classify/sample_training_set.py`). `ml/classify/train.py` trains it on the real CUAD split
  with a contract-grouped holdout, and `ml/classify/transformer.py` fine-tunes Legal-BERT on the
  same split; the fine-tuning run needs a GPU, so it's meant for a Colab T4 or similar, not a
  laptop.
- **Retrieval** (`ml/retrieve/hybrid.py`) is real code against a real OpenSearch query shape, but
  the index has nothing in it yet. `pipelines/seed/cuad_precedent.py` writes gold segments as
  precedent rows; the existing outbox relay (`services/worker/outbox.py`) is what gets them into
  OpenSearch, by design (see ADR 2).
- **The 150 gold-labeled clauses** don't exist as data. See
  [`eval/fixtures/gold_clauses.schema.md`](eval/fixtures/gold_clauses.schema.md) for the schema and
  the labeling process, including the second-rater kappa check. Three illustrative rows stand in
  for CI. `pipelines/sampling/draw_gold_sample.py` draws the 150 candidates; labeling them is
  manual work no script can do.
- **The Word add-in's Office.js calls** (locate, highlight, tracked-change apply) type-check
  against `@types/office-js` but haven't run inside a live Word host yet.
- **`eval/thresholds.yaml`** still holds placeholder numbers. They get replaced with real ones
  once the suites above have a real run to measure against.

## Data sources and attribution

- **CUAD v1**: 510 commercial contracts, lawyer-labeled spans across 41 categories. The Atticus
  Project, CC BY 4.0.
- **ACORD**: expert-rated query/clause pairs, CC BY 4.0, for retrieval evaluation.

Full attribution, download dates and license terms: [`docs/data-sources.md`](docs/data-sources.md).

## Sample playbooks

The eight clause-type ladders in `pipelines/seed/sample_playbooks.py` are not any real firm's
guidance. They're written from public drafting commentary as a stand-in so the product has
something realistic to run against. The web app labels anything seeded from this fixture "sample"
on screen.
