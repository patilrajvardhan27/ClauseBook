# Fine-tunes legal-bert-base-uncased on the real CUAD gold segments.
#
# Runs on a CUDA GPU or Apple silicon (MPS); on CPU it is impractically slow.
# Reads the same data/gold/segments.csv the TF-IDF baseline trains on
# (ml/classify/train.py) and the same contract-grouped folds, so the two
# numbers are comparable. Saves the best fold's model to ml/checkpoints/legal-bert.
# The worker's classify stage does not load it yet; it still serves the baseline.
#
# Three things separate this from a plain fine-tune, because 41 mostly rare labels
# collapse to "predict nothing" under a fixed 0.5 cutoff and unweighted loss:
#   - positive-class weights in the loss, so a rare label's positives are not drowned out
#   - a decision threshold picked on a validation slice of each fold's training
#     contracts, never on the held-out fold it is scored against
#   - a higher learning rate than the usual 2e-5, since the head starts from scratch
#
# Usage: PYTHONPATH=.:libs python3 ml/classify/transformer.py
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score, precision_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.preprocessing import MultiLabelBinarizer

from ml.classify.train import N_FOLDS, load_gold_rows

CHECKPOINT_DIR = Path("ml/checkpoints/legal-bert")
BASE_MODEL = "nlpaueb/legal-bert-base-uncased"
MAX_LENGTH = 256
BATCH_SIZE = 16
LEARNING_RATE = 5e-5
NUM_EPOCHS = 5
VALIDATION_SHARE = 0.1
MAX_POS_WEIGHT = 10.0
THRESHOLD_GRID = np.arange(0.05, 0.96, 0.05)


def _sigmoid(logits: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-logits))


# Macro precision and macro F1 over every label, the same definition train.py reports.
def macro_scores(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "macro_precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


# Square-root-damped negative/positive ratio per label, capped so one rare label cannot dominate.
def _positive_weights(label_matrix: np.ndarray) -> np.ndarray:
    positives = np.maximum(label_matrix.sum(axis=0), 1)
    negatives = len(label_matrix) - positives
    return np.minimum(np.sqrt(negatives / positives), MAX_POS_WEIGHT).astype("float32")


# The global cutoff that maximises macro F1 on the validation slice.
def pick_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    scores = [macro_scores(y_true, (probabilities >= t).astype(int))["macro_f1"] for t in THRESHOLD_GRID]
    return float(THRESHOLD_GRID[int(np.argmax(scores))])


# Builds a tokenized HF Dataset with multi-hot label vectors from the gold rows.
def _build_dataset(rows: list[dict], binarizer: MultiLabelBinarizer, tokenizer):
    from datasets import Dataset

    labels = binarizer.transform([r["categories"] for r in rows]).astype("float32")
    dataset = Dataset.from_dict({"text": [r["text"] for r in rows], "labels": labels.tolist()})
    return dataset.map(
        lambda batch: tokenizer(batch["text"], truncation=True, max_length=MAX_LENGTH, padding="max_length"),
        batched=True,
    )


def _weighted_trainer_class():
    import torch
    from transformers import Trainer

    # Trainer whose loss up-weights each label's positives.
    class WeightedTrainer(Trainer):
        def __init__(self, *args, pos_weight: np.ndarray, **kwargs):
            super().__init__(*args, **kwargs)
            self._pos_weight = torch.tensor(pos_weight)

        def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=self._pos_weight.to(outputs.logits.device))
            loss = loss_fn(outputs.logits, labels)
            return (loss, outputs) if return_outputs else loss

    return WeightedTrainer


# Fine-tunes on train_rows, tunes the threshold on val_rows, scores on eval_rows.
def _train_one_fold(train_rows, val_rows, eval_rows, binarizer):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, TrainingArguments

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(binarizer.classes_), problem_type="multi_label_classification"
    )
    train_set, val_set, eval_set = (_build_dataset(r, binarizer, tokenizer) for r in (train_rows, val_rows, eval_rows))

    args = TrainingArguments(
        output_dir=str(CHECKPOINT_DIR / "tmp"),
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        num_train_epochs=NUM_EPOCHS,
        warmup_steps=0.1,
        eval_strategy="no",
        save_strategy="no",
        report_to="none",
    )
    train_labels = np.array(train_set["labels"])
    trainer = _weighted_trainer_class()(
        model=model, args=args, train_dataset=train_set, pos_weight=_positive_weights(train_labels)
    )
    trainer.train()

    val_probs = _sigmoid(trainer.predict(val_set).predictions)
    threshold = pick_threshold(np.array(val_set["labels"]), val_probs)
    eval_probs = _sigmoid(trainer.predict(eval_set).predictions)
    metrics = macro_scores(np.array(eval_set["labels"]), (eval_probs >= threshold).astype(int))
    return model, tokenizer, {**metrics, "threshold": threshold}


# Holds out a share of the fold's training contracts for threshold selection.
def _split_validation(train_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    groups = [r["contract_id"] for r in train_rows]
    splitter = GroupShuffleSplit(n_splits=1, test_size=VALIDATION_SHARE, random_state=0)
    fit_idx, val_idx = next(splitter.split(train_rows, groups=groups))
    return [train_rows[i] for i in fit_idx], [train_rows[i] for i in val_idx]


def _fold_dir(fold_idx: int) -> Path:
    return CHECKPOINT_DIR / f"fold_{fold_idx}"


# Trains and scores one fold in this process and writes its model and metrics under fold_<n>/.
def run_fold(fold_idx: int) -> None:
    rows = load_gold_rows()
    binarizer = MultiLabelBinarizer().fit([r["categories"] for r in rows])
    groups = [r["contract_id"] for r in rows]
    train_idx, eval_idx = list(GroupKFold(n_splits=N_FOLDS).split(rows, groups=groups))[fold_idx]

    fit_rows, val_rows = _split_validation([rows[i] for i in train_idx])
    model, tokenizer, metrics = _train_one_fold(fit_rows, val_rows, [rows[i] for i in eval_idx], binarizer)

    out = _fold_dir(fold_idx)
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out)
    tokenizer.save_pretrained(out)
    (out / "metrics.json").write_text(json.dumps(metrics))
    print(
        f"Fold {fold_idx}: macro_f1 {metrics['macro_f1']:.3f}, "
        f"macro_precision {metrics['macro_precision']:.3f}, threshold {metrics['threshold']:.2f}",
        flush=True,
    )


# Averages every fold's metrics and promotes the best fold's model to the checkpoint root.
def summarize() -> None:
    metrics = [json.loads((_fold_dir(i) / "metrics.json").read_text()) for i in range(N_FOLDS)]
    print(
        f"Mean over {N_FOLDS} folds: macro_f1 {np.mean([m['macro_f1'] for m in metrics]):.3f}, "
        f"macro_precision {np.mean([m['macro_precision'] for m in metrics]):.3f}"
    )
    best = int(np.argmax([m["macro_f1"] for m in metrics]))
    for item in _fold_dir(best).iterdir():
        shutil.copy2(item, CHECKPOINT_DIR / item.name)
    print(f"Saved fold {best}'s model to {CHECKPOINT_DIR}")


# One fresh process per fold: PyTorch keeps device memory after a fold ends and a single
# long-lived process swaps itself to a crawl on a 16 GB machine. Finished folds are skipped,
# so an interrupted run resumes where it stopped.
def main() -> None:
    if len(sys.argv) > 1:
        run_fold(int(sys.argv[1]))
        return
    for fold_idx in range(N_FOLDS):
        if not (_fold_dir(fold_idx) / "metrics.json").exists():
            subprocess.run([sys.executable, __file__, str(fold_idx)], check=True)
    summarize()


if __name__ == "__main__":
    main()
