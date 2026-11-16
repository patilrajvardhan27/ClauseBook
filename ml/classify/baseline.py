# TF-IDF + one-vs-rest logistic regression multi-label baseline, the number the fine-tuned model must beat.
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer


# A fitted TF-IDF vectorizer, label binarizer, classifier and per-class thresholds.
@dataclass
class BaselineClassifier:
    vectorizer: TfidfVectorizer
    binarizer: MultiLabelBinarizer
    model: OneVsRestClassifier
    thresholds: dict[str, float]

    # Fits the vectorizer, binarizer and classifier on a training set.
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

    # Returns per-class probabilities for a batch of texts.
    def predict_proba(self, texts: list[str]) -> np.ndarray:
        features = self.vectorizer.transform(texts)
        return self.model.predict_proba(features)

    # Picks the labels whose probability clears each class's threshold.
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

    # Updates per-class thresholds after eval tunes them on a validation split.
    def set_thresholds(self, thresholds: dict[str, float]) -> None:
        self.thresholds.update(thresholds)
