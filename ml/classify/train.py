# Trains the TF-IDF baseline on the real CUAD gold segments, split by contract, and reports honest numbers.
#
# Run after pipelines/gold/run_gold.py has written data/gold/segments.csv.
# GroupKFold on contract_id, not a random split: contracts reuse the same
# boilerplate, so a random split puts near-duplicate clauses in both train
# and test and inflates every score reported downstream.
#
# Usage: PYTHONPATH=.:libs python3 ml/classify/train.py
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score, precision_score
from sklearn.model_selection import GroupKFold

from ml.classify.baseline import BaselineClassifier

GOLD_SEGMENTS_PATH = Path("data/gold/segments.csv")
N_FOLDS = 5


# One gold segment's text, contract id, heading and the categories its span overlap gave it.
def _load_rows() -> list[dict]:
    with GOLD_SEGMENTS_PATH.open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["categories"] = json.loads(row["categories_json"])
    return [row for row in rows if row["categories"]]  # unlabeled segments teach the model nothing


# Runs GroupKFold by contract_id and reports macro precision and per-label F1 on the held-out fold.
def cross_validate(rows: list[dict]) -> dict:
    texts = [r["text"] for r in rows]
    labels = [r["categories"] for r in rows]
    groups = [r["contract_id"] for r in rows]

    gkf = GroupKFold(n_splits=N_FOLDS)
    fold_macro_precision: list[float] = []
    per_label_f1: dict[str, list[float]] = {}

    for train_idx, test_idx in gkf.split(texts, groups=groups):
        train_texts = [texts[i] for i in train_idx]
        train_labels = [labels[i] for i in train_idx]
        test_texts = [texts[i] for i in test_idx]
        test_labels = [labels[i] for i in test_idx]

        model = BaselineClassifier.fit(train_texts, train_labels)
        predicted = model.predict_labels(test_texts)

        y_true = model.binarizer.transform(test_labels)
        y_pred = model.binarizer.transform(predicted)

        fold_macro_precision.append(precision_score(y_true, y_pred, average="macro", zero_division=0))
        f1_per_class = f1_score(y_true, y_pred, average=None, zero_division=0)
        for label, score in zip(model.binarizer.classes_, f1_per_class):
            per_label_f1.setdefault(label, []).append(score)

    return {
        "macro_precision": float(np.mean(fold_macro_precision)),
        "per_label_f1": {label: float(np.mean(scores)) for label, scores in per_label_f1.items()},
    }


# Reports how often a segment's label disagrees with what its heading would suggest.
def heading_disagreement_rate(rows: list[dict]) -> float:
    disagreements = 0
    headed_rows = [r for r in rows if r.get("heading")]
    for row in headed_rows:
        heading_lower = row["heading"].lower()
        if not any(category.lower() in heading_lower for category in row["categories"]):
            disagreements += 1
    return disagreements / len(headed_rows) if headed_rows else 0.0


def main() -> None:
    rows = _load_rows()
    print(f"Loaded {len(rows)} labeled gold segments across {len({r['contract_id'] for r in rows})} contracts")

    results = cross_validate(rows)
    print(f"Macro precision (GroupKFold by contract, {N_FOLDS} folds): {results['macro_precision']:.3f}")
    print("Per-label F1:")
    for label, score in sorted(results["per_label_f1"].items(), key=lambda kv: -kv[1]):
        print(f"  {label}: {score:.3f}")

    rate = heading_disagreement_rate(rows)
    print(f"Heading disagreement rate: {rate:.1%} of headed segments carry a label their heading doesn't name")


if __name__ == "__main__":
    main()
