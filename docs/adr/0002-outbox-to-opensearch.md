# ADR 2: Outbox pattern to OpenSearch, never a dual write

## Status
Accepted

## Context
Precedent needs to be searchable with BM25 and kNN, which means it lives in
OpenSearch as well as Postgres. Writing to both on every precedent change
risks one write succeeding and the other failing, leaving the two stores
disagreeing with no way to tell which one is right.

## Decision
Postgres stays the single source of truth. A precedent write also writes an
`outbox_event` row in the same transaction. A relay (`services/worker/outbox.py`)
reads unpublished outbox rows and indexes them into OpenSearch, marking them
published once the bulk request succeeds.

## Consequences
OpenSearch can be dropped and rebuilt from Postgres at any time with no data
loss, since it holds nothing that Postgres does not already have. Indexing
lags writes by however long the relay takes to run, which is fine for
precedent search and would not be fine for a field the UI needs read-after-write
consistency on.
