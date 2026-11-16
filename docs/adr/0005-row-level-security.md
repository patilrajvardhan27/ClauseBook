# ADR 5: Tenant isolation enforced in Postgres, not only in application code

## Status
Accepted

## Context
Every ontology table and every review carries `firm_id`. Relying on every
query in the API and worker to remember a `WHERE firm_id = ...` clause is one
missed filter away from one firm reading another firm's playbook.

## Decision
Row-level security policies on `firm`-scoped tables key off a session
variable (`app.current_firm_id`) set once per request/job, so the database
itself refuses a query outside that firm's rows regardless of what the
application code does or forgets.

## Consequences
A bug in a router or a worker stage cannot leak data across firms; the
database is the last line of defense, not the application. The cost is a
`SET LOCAL` call at the start of every transaction and a short setup step in
migrations, both one-time.
