"""TF-IDF + one-vs-rest logistic regression multi-label baseline.

This exists to give the fine-tuned transformer (ml/classify/transformer.py,
trained separately once CUAD is pulled locally) a number to beat. A
classifier that cannot clear a bag-of-words baseline is not worth the GPU
time, so this runs first and the gate in eval/thresholds.yaml holds the
line.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer


@dataclass
class BaselineClassifier:
    vectorizer: TfidfVectorizer
    binarizer: MultiLabelBinarizer
    model: OneVsRestClassifier
    thresholds: dict[str, float]

    @classmethod
    def fit(cls, texts: list[str], labels: list[list[str]]) -> BaselineClassifier:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), min_df=2, max_features=50_000, sublinear_tf=True, analyzer="word"
        )
        features = vectorizer.fit_transform(texts)

        binarizer = MultiLabelBinarizer()
        targets = binarizer.fit_transform(labels)

        model = OneVsRestClassifier(LogisticRegression(max_iter=1000, class_weight="balanced"))
        model.fit(features, targets)

        # Default threshold 0.5 for every class until eval tunes per-class thresholds on a holdout split.
        thresholds = {label: 0.5 for label in binarizer.classes_}
        return cls(vectorizer=vectorizer, binarizer=binarizer, model=model, thresholds=thresholds)

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        features = self.vectorizer.transform(texts)
        return self.model.predict_proba(features)

    def predict_labels(self, texts: list[str]) -> list[list[str]]:
        probabilities = self.predict_proba(texts)
        results: list[list[str]] = []
        for row in probabilities:
            picked = [
                label
                for label, prob in zip(self.binarizer.classes_, row)
                if prob >= self.thresholds.get(label, 0.5)
            ]
            results.append(picked)
        return results

    def set_thresholds(self, thresholds: dict[str, float]) -> None:
        """Called by ml/eval after tuning each class's threshold on a validation
        split for precision at 80% recall, CUAD's own reporting metric."""
        self.thresholds.update(thresholds)
