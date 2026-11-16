# Stage 3: multi-label clause-type classification, ONNX model if trained, TF-IDF baseline otherwise.
from __future__ import annotations

import os

from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage

_MODEL_PATH = os.environ.get("CLAUSEBOOK_CLASSIFIER_ONNX", "ml/checkpoints/classifier.onnx")


# Classifies every segment's clause type.
class ClassifyStage(Stage):
    name = "classify"

    def run(self, ctx: ReviewContext) -> StageResult:
        predictions = self._predict([s.text for s in ctx.segments])
        for segment, labels in zip(ctx.segments, predictions):
            segment.predicted_labels = labels  # consumed by extract.py in the same run, not persisted as a column
        return StageResult(ok=True, message=f"classified {len(ctx.segments)} segments")

    # Picks the ONNX model if one has been trained, else the baseline.
    def _predict(self, texts: list[str]) -> list[list[str]]:
        if os.path.exists(_MODEL_PATH):
            return self._predict_onnx(texts)
        return self._predict_baseline(texts)

    # Loads the int8 ONNX export; not yet wired in, so this still calls the baseline.
    def _predict_onnx(self, texts: list[str]) -> list[list[str]]:
        return self._predict_baseline(texts)

    # Runs the cached TF-IDF baseline classifier.
    def _predict_baseline(self, texts: list[str]) -> list[list[str]]:
        model = _load_cached_baseline()
        if model is None:
            return [[] for _ in texts]
        return model.predict_labels(texts)


_CACHED_BASELINE = None


# Trains the baseline once per process on the bundled sample set.
def _load_cached_baseline():
    global _CACHED_BASELINE
    if _CACHED_BASELINE is None:
        from ml.classify.baseline import BaselineClassifier
        from ml.classify.sample_training_set import SAMPLE_LABELS, SAMPLE_TEXTS

        _CACHED_BASELINE = BaselineClassifier.fit(SAMPLE_TEXTS, SAMPLE_LABELS)
    return _CACHED_BASELINE
