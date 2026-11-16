# ADR 6: Customer documents never train a model

## Status
Accepted

## Context
A firm's uploaded contracts and its playbook are confidential by definition.
Using them to fine-tune a shared classifier or embedding model would mean
one firm's draft language shaping predictions another firm sees.

## Decision
Training data for the classifier and the embedding model comes only from
CUAD (CC BY 4.0, public). A firm's own documents feed only that firm's own
precedent index in OpenSearch, scoped by `firm_id`, and are never copied into
a training set.

## Consequences
Model quality is bounded by what CUAD covers, so an unusual clause type a
firm specializes in will not improve the shared model over time -- the
precedent index is where that firm's own experience accumulates instead.
This is a deliberate trade against the alternative, which is a model that
quietly leaks one client's drafting into another's results.
