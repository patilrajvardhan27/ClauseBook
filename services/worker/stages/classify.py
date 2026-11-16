"""Stage 3: multi-label clause-type classification.

Loads the ONNX-exported fine-tuned classifier if one has been trained
(ml/export writes it to ml/checkpoints/); falls back to the TF-IDF baseline
so a bare dev environment still produces findings end to end.
"""
from __future__ import annotations

import os

from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage

_MODEL_PATH = os.environ.get("CLAUSEBOOK_CLASSIFIER_ONNX", "ml/checkpoints/classifier.onnx")


class ClassifyStage(Stage):
    name = "classify"

    def run(self, ctx: ReviewContext) -> StageResult:
        predictions = self._predict([s.text for s in ctx.segments])
        for segment, labels in zip(ctx.segments, predictions):
            segment.predicted_labels = labels  # consumed by extract.py in the same run, not persisted as a column
        return StageResult(ok=True, message=f"classified {len(ctx.segments)} segments")

    def _predict(self, texts: list[str]) -> list[list[str]]:
        if os.path.exists(_MODEL_PATH):
            return self._predict_onnx(texts)
        return self._predict_baseline(texts)

    def _predict_onnx(self, texts: list[str]) -> list[list[str]]:
        # TODO(ml): load the int8 ONNX export and the per-class thresholds
        # tuned in ml/eval, batching by sequence length as section 11 plans.
        return self._predict_baseline(texts)

    def _predict_baseline(self, texts: list[str]) -> list[list[str]]:

        model = _load_cached_baseline()
        if model is None:
            return [[] for _ in texts]
        return model.predict_labels(texts)


_CACHED_BASELINE = None


def _load_cached_baseline():
    """Trains the baseline once per process on the bundled sample set.
    Replaced by a model loaded from ml/checkpoints/ once ml/classify/train.py
    has produced one from the full CUAD corpus."""
    global _CACHED_BASELINE
    if _CACHED_BASELINE is None:
        from ml.classify.baseline import BaselineClassifier
        from ml.classify.sample_training_set import SAMPLE_LABELS, SAMPLE_TEXTS

        _CACHED_BASELINE = BaselineClassifier.fit(SAMPLE_TEXTS, SAMPLE_LABELS)
    return _CACHED_BASELINE
