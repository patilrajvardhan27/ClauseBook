# Clausebook eval report
- generated: 2026-11-16T15:50:14.889652+00:00
- commit: 0310735
- gold data version: no eval/fixtures/gold_clauses.csv yet

## Extraction (illustrative fixture)
- rows: 3
- non-empty extraction rate: 1.00
- gate (exact_match_min): 0.6

## Classification
- macro precision (GroupKFold by contract): 0.599
  - Governing Law: F1 0.902
  - Insurance: F1 0.887
  - Parties: F1 0.842
  - Cap On Liability: F1 0.841
  - Audit Rights: F1 0.818
  - Anti-Assignment: F1 0.809
  - License Grant: F1 0.775
  - Expiration Date: F1 0.744
  - Document Name: F1 0.742
  - No-Solicit Of Employees: F1 0.734
  - Revenue/Profit Sharing: F1 0.725
  - Renewal Term: F1 0.713
  - Rofr/Rofo/Rofn: F1 0.710
  - Agreement Date: F1 0.707
  - Covenant Not To Sue: F1 0.660
  - Warranty Duration: F1 0.656
  - Irrevocable Or Perpetual License: F1 0.642
  - Notice Period To Terminate Renewal: F1 0.637
  - Source Code Escrow: F1 0.630
  - Minimum Commitment: F1 0.629
  - Ip Ownership Assignment: F1 0.625
  - Termination For Convenience: F1 0.615
  - Uncapped Liability: F1 0.577
  - Liquidated Damages: F1 0.564
  - Post-Termination Services: F1 0.560
  - Non-Transferable License: F1 0.555
  - Effective Date: F1 0.555
  - Non-Compete: F1 0.515
  - Exclusivity: F1 0.513
  - Change Of Control: F1 0.512
  - Joint Ip Ownership: F1 0.502
  - Third Party Beneficiary: F1 0.464
  - Affiliate License-Licensee: F1 0.441
  - Volume Restriction: F1 0.408
  - No-Solicit Of Customers: F1 0.322
  - Affiliate License-Licensor: F1 0.286
  - Competitive Restriction Exception: F1 0.276
  - Non-Disparagement: F1 0.272
  - Most Favored Nation: F1 0.196
  - Unlimited/All-You-Can-Eat-License: F1 0.178
  - Price Restrictions: F1 0.000
- heading disagreement rate: 94.8%

## Retrieval (ACORD)
- bm25: nDCG@5 0.151, Recall@20 0.058
- knn: nDCG@5 0.146, Recall@20 0.077
- hybrid: nDCG@5 0.180, Recall@20 0.080
- hybrid+rerank: nDCG@5 0.193, Recall@20 0.080

## Placement
Not run: eval/fixtures/gold_clauses.csv missing. See its schema doc.

## Cost and latency
Not run: needs the Docker Compose stack up and 20+ contracts fed through it. See ml/eval/perf.py.
