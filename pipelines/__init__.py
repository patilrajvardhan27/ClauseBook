"""Medallion-layout data pipelines: bronze (raw), silver (normalized), gold
(segmented and labeled). Each layer is idempotent -- re-running a stage on
data it has already processed adds zero new rows."""
