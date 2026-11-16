# ADR 4: Findings stream over SSE as they finish

## Status
Accepted

## Context
A 100-page contract can take well over a minute to review end to end. Making
a lawyer stare at a blank screen for that long, then dumping forty findings
on them at once, is a worse experience than the wait itself.

## Decision
`GET /v1/reviews/{id}/events` is a Server-Sent Events stream. The worker
writes each finding as its own committed row; the API polls the findings
table and emits `finding_ready` the moment a new row appears, alongside
`progress`, `segment_found`, `done` and `error`.

## Consequences
The first finding reaches the task pane in roughly the time one clause takes
to process, not the whole document. The stream is stateless -- a refreshed
task pane just reconnects and replays what already exists -- at the cost of
a one-second poll interval instead of true push.
