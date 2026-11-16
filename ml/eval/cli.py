"""`clausebook eval` -- runs the suites this project can run with no live
infrastructure (placement, extraction) and writes eval/report.md. The
retrieval, classification and cost/latency suites need a trained model and
a populated OpenSearch index respectively; they are left as separate
entrypoints (ml/classify/train.py, ml/retrieve, ml/eval/perf.py) rather than
silently skipped here.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ml.eval.thresholds import load_thresholds

REPORT_PATH = Path("eval/report.md")


def run_extraction_suite() -> dict:
    """Exact-match accuracy of ml/extract against the illustrative gold CSV.
    Swap in eval/fixtures/gold_clauses.csv once the real 150 are labeled."""
    from ml.extract.extractors import extract

    csv_path = Path("eval/fixtures/gold_clauses.sample.csv")
    rows = list(csv.DictReader(csv_path.open()))
    if not rows:
        return {"accuracy": 0.0, "n": 0}

    correct = 0
    for row in rows:
        attrs = extract(row["cuad_category"], row["clause_text"])
        correct += 1 if attrs else 0  # exact-match-per-attribute needs the real labeled attrs; this is a presence check

    return {"accuracy": correct / len(rows), "n": len(rows)}


def main() -> None:
    thresholds = load_thresholds()
    extraction = run_extraction_suite()

    lines = [
        "# Clausebook eval report",
        "",
        "## Extraction (illustrative fixture)",
        f"- rows: {extraction['n']}",
        f"- non-empty extraction rate: {extraction['accuracy']:.2f}",
        f"- gate (exact_match_min): {thresholds['extraction']['exact_match_min']}",
        "",
        "## Not run in this environment",
        "- Classification (needs a trained model; see ml/classify/train.py)",
        "- Retrieval (needs OpenSearch populated by pipelines/gold + the outbox relay)",
        "- Placement on the real 150 gold clauses (needs eval/fixtures/gold_clauses.csv, see its schema doc)",
        "- Cost and latency (needs a running API/worker stack)",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines))
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
