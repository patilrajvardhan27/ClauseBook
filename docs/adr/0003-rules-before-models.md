# ADR 3: Deterministic rules run before any model

## Status
Accepted

## Context
Term extraction and placement could both run entirely on an LLM: read the
clause, ask it for the cap multiple, ask it where that sits on the ladder.
That is fast to build and slow to trust.

## Decision
Regex and rule-based extraction (`ml/extract`) and a pure rule engine for
placement (`libs/clausebook_core/placement`) run first, on every clause. An
LLM is reserved for wording the final redline and for filling an attribute a
rule returns nothing for -- never for deciding where a clause sits on the
ladder.

## Consequences
Placement is auditable: every decision traces to a condition and a value
that can be checked by eye. It is also free and instant, which matters for
the preview endpoint lawyers use while editing a playbook. The cost is that
a clause worded in a way the rules do not anticipate is not extracted; the
plan's eval harness exists to catch that gap and grow the rule set rather
than silently falling back to a guess.
