# `clausebook eval` -- runs every suite it can reach and writes eval/report.md with what it found.
#
# Each section is wrapped so a missing dependency (no trained model, no
# live OpenSearch, no gold CSV) becomes one line in the report instead of
# a crash, since most people running this will have some pieces and not
# others.
from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from ml.eval.thresholds import load_thresholds

REPORT_PATH = Path("eval/report.md")
GOLD_CLAUSES_PATH = Path("eval/fixtures/gold_clauses.csv")
GOLD_CLAUSES_SAMPLE_PATH = Path("eval/fixtures/gold_clauses.sample.csv")


# Current commit hash, or "unknown" outside a git checkout.
def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001 -- this CLI must never crash on a missing git checkout
        return "unknown"


# SHA-256 of the real gold clause file, so a report can be tied to the exact data it ran against.
def _data_version() -> str:
    if not GOLD_CLAUSES_PATH.exists():
        return "no eval/fixtures/gold_clauses.csv yet"
    return hashlib.sha256(GOLD_CLAUSES_PATH.read_bytes()).hexdigest()[:12]


# Checks extraction against the real gold CSV if labeled, else the illustrative sample.
def run_extraction_suite() -> tuple[str, dict]:
    from ml.extract.extractors import extract

    csv_path = GOLD_CLAUSES_PATH if GOLD_CLAUSES_PATH.exists() else GOLD_CLAUSES_SAMPLE_PATH
    label = "real gold set" if csv_path == GOLD_CLAUSES_PATH else "illustrative fixture"
    rows = list(csv.DictReader(csv_path.open()))
    if not rows:
        return label, {"accuracy": 0.0, "n": 0}

    correct = 0
    for row in rows:
        attrs = extract(row["cuad_category"], row["clause_text"])
        correct += 1 if attrs else 0  # exact-match-per-attribute needs the real labeled attrs; this is a presence check

    return label, {"accuracy": correct / len(rows), "n": len(rows)}


GOLD_SEGMENTS_PATH = Path("data/gold/segments.csv")


# Trains and cross-validates the baseline classifier if CUAD gold segments have been pulled.
def run_classification_suite() -> list[str]:
    if not GOLD_SEGMENTS_PATH.exists():
        return ["Not run: data/gold/segments.csv missing. Run pipelines/gold/run_gold.py first."]

    from ml.classify.train import cross_validate, heading_disagreement_rate, load_gold_rows

    rows = load_gold_rows()
    results = cross_validate(rows)
    lines = [f"- macro precision (GroupKFold by contract): {results['macro_precision']:.3f}"]
    for label, score in sorted(results["per_label_f1"].items(), key=lambda kv: -kv[1]):
        lines.append(f"  - {label}: F1 {score:.3f}")
    lines.append(f"- heading disagreement rate: {heading_disagreement_rate(rows):.1%}")
    return lines


# Runs the ACORD comparison if the fixture and a live OpenSearch are both reachable.
def run_retrieval_suite() -> list[str]:
    acord_path = Path("eval/fixtures/acord_queries.csv")
    if not acord_path.exists():
        return ["Not run: eval/fixtures/acord_queries.csv missing. See its schema doc."]

    try:
        from ml.eval.acord_eval import run_acord_eval

        results = run_acord_eval()
    except Exception as exc:  # noqa: BLE001 -- live OpenSearch not reachable, or index empty
        return [f"Not run: {exc}"]

    return [f"- {mode}: nDCG@5 {m['ndcg_at_5']:.3f}, Recall@20 {m['recall_at_20']:.3f}" for mode, m in results.items()]


# Scores the placement engine on the real gold clauses if a live Postgres is reachable.
def run_placement_suite() -> list[str]:
    if not GOLD_CLAUSES_PATH.exists():
        return ["Not run: eval/fixtures/gold_clauses.csv missing. See its schema doc."]
    return ["Not run: wiring this suite to a live playbook needs eval/fixtures/gold_clauses.csv and a reachable database."]


def main() -> None:
    thresholds = load_thresholds()
    extraction_label, extraction = run_extraction_suite()

    lines = [
        "# Clausebook eval report",
        f"- generated: {datetime.now(UTC).isoformat()}",
        f"- commit: {_git_commit()}",
        f"- gold data version: {_data_version()}",
        "",
        f"## Extraction ({extraction_label})",
        f"- rows: {extraction['n']}",
        f"- non-empty extraction rate: {extraction['accuracy']:.2f}",
        f"- gate (exact_match_min): {thresholds['extraction']['exact_match_min']}",
        "",
        "## Classification",
        *run_classification_suite(),
        "",
        "## Retrieval (ACORD)",
        *run_retrieval_suite(),
        "",
        "## Placement",
        *run_placement_suite(),
        "",
        "## Cost and latency",
        "Not run: needs the Docker Compose stack up and 20+ contracts fed through it. See ml/eval/perf.py.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines))
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
