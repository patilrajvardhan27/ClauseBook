# Data sources

## CUAD v1

- **Source:** The Atticus Project, via Zenodo (`pipelines/bronze/cuad.py` pulls
  `https://zenodo.org/record/4595826/files/CUAD_v1.zip`).
- **License:** CC BY 4.0.
- **Contents:** 510 commercial contracts pulled from SEC EDGAR, with lawyer-labeled spans across
  41 clause categories.
- **Used for:** segmentation boundary evaluation, the classifier's training and test split
  (grouped by contract so no contract's segments cross the train/test boundary), the precedent
  corpus, and market-percentile statistics.
- **Attribution:** Hendrycks, Dan, et al. "CUAD: An Expert-Annotated NLP Dataset for Legal
  Contract Review." NeurIPS 2021 Datasets and Benchmarks Track.

## ACORD

- **License:** CC BY 4.0.
- **Contents:** expert-rated query/clause pairs across nine categories.
- **Used for:** retrieval evaluation (NDCG@5, Recall@20) of the hybrid BM25 + kNN search.

## Sample playbooks

Written by hand from public drafting commentary (ABA model negotiated terms, published playbook
articles), not copied from any firm's real guidance. Labeled "sample" wherever they appear in the
web app.

## Gold placement labels

150 hand-labeled clauses, scored against the placement engine for matched-position and fallback
accuracy. Not included as data in this repository. See
[`eval/fixtures/gold_clauses.schema.md`](../eval/fixtures/gold_clauses.schema.md) for the format
and the labeling process, including the second-rater Cohen's kappa check to run before trusting
the full set.

## Download dates

Recorded in `data/bronze/*/manifest.json` at download time (not committed; `data/` is
gitignored). Each manifest carries the source URL, the SHA-256 of the downloaded archive, and the
license string, per the rule that every dataset's provenance must be checkable after the fact.
