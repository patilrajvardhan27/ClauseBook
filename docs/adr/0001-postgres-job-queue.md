# ADR 1: Postgres job queue instead of a message broker

## Status
Accepted

## Context
A review needs background work: parsing, segmenting, classifying, extracting,
retrieving, placing and redlining a document without blocking the API request
that started it. The obvious answer is a broker (Redis, RabbitMQ, SQS).

## Decision
Use a plain Postgres table (`job`) with `SELECT ... FOR UPDATE SKIP LOCKED`
instead. The API writes the job row and the review row in the same
transaction, so a job can never exist without its review or the reverse.

## Consequences
One fewer system to run, deploy and monitor. The queue inherits Postgres's
durability for free. Throughput tops out well below a dedicated broker, but a
single-firm deployment will not get near the roughly 50 jobs/second where
this starts to matter. Revisit if usage grows past that.
