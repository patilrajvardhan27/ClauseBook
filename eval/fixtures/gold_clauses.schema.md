# Gold clause label schema

150 hand-labeled clauses are what section 10 of the build plan scores the
placement engine against. They are not included in this repository as
data, because they do not exist yet -- labeling them is a manual task for
whoever runs this project, not something to fabricate.

## Format

`eval/fixtures/gold_clauses.csv`, one row per clause:

| column | type | meaning |
|---|---|---|
| `clause_id` | string | stable id, e.g. `gold-001` |
| `cuad_category` | string | one of the eight v1 clause types |
| `clause_text` | string | the clause as drafted by the counterparty |
| `deal_context_json` | string | JSON: `{"party_role": ..., "deal_size_band": ..., "counterparty_type": ...}` |
| `gold_matched_position_id` | string | the position UUID a lawyer says this clause actually sits at |
| `gold_proposed_position_id` | string | the position UUID a lawyer would propose as the fallback (empty if none needed) |
| `labeled_by` | string | labeler identifier, e.g. `primary` or `second_rater` |

## Process (do this yourself; do not skip it)

1. Pull 150 clauses across the eight v1 categories from the CUAD gold
   segments (`pipelines/gold/segments.py`), weighted toward categories with
   fewer examples so no category is left with under 10 labels.
2. Label all 150 against the sample playbook's ladder (or your own, if you
   have replaced it) using the preview endpoint to sanity-check each call.
3. Ask one other person -- a law student or a colleague who reads
   contracts -- to label 50 of the 150 blind, with no view of your labels.
4. Run `python3 ml/eval/kappa.py eval/fixtures/gold_clauses.csv` to get
   Cohen's kappa on the 50 shared rows.
5. If kappa is under 0.6, the position definitions are ambiguous, not the
   labelers. Tighten the conditions in the playbook (section 4.3's
   `position_condition` rows) and relabel the 50 before trusting the rest.

## Illustrative rows (not real labels -- shape only)

`eval/fixtures/gold_clauses.sample.csv` holds three rows built from the
sample playbook seeded by `pipelines/seed/run_seed.py`, so `ml/eval/kappa.py`
and `ml/eval/placement_eval.py` have something to run against in CI without
requiring the real 150-row file. They are marked `labeled_by: illustrative`
and must never be counted toward the real gold set or its kappa score.
