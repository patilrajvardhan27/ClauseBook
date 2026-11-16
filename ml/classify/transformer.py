# Fine-tunes legal-bert-base-uncased on the real CUAD gold segments; needs a GPU to run in reasonable time.
#
# Meant for a Colab T4 or similar, not this project's dev environment.
# Reads the same data/gold/segments.csv the TF-IDF baseline trains on
# (ml/classify/train.py) and the same contract-grouped split, so the two
# numbers are comparable. Saves whichever model wins to ml/checkpoints/,
# which services/worker/stages/classify.py already knows to look for.
#
# Usage (on a GPU machine): PYTHONPATH=.:libs python3 ml/classify/transformer.py
from __future__ import annotations

import csv
import json
from pathlib import Path

from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import MultiLabelBinarizer

GOLD_SEGMENTS_PATH = Path("data/gold/segments.csv")
CHECKPOINT_DIR = Path("ml/checkpoints/legal-bert")
BASE_MODEL = "nlpaueb/legal-bert-base-uncased"
N_FOLDS = 5
MAX_LENGTH = 256
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
NUM_EPOCHS = 4


# Loads labeled gold segments the same way ml/classify/train.py does, so both models see identical data.
def _load_rows() -> list[dict]:
    with GOLD_SEGMENTS_PATH.open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["categories"] = json.loads(row["categories_json"])
    return [row for row in rows if row["categories"]]


# Builds a HF Dataset with multi-hot label vectors from the gold rows.
def _build_dataset(rows: list[dict], binarizer: MultiLabelBinarizer):
    from datasets import Dataset

    labels = binarizer.transform([r["categories"] for r in rows]).astype("float32")
    return Dataset.from_dict({"text": [r["text"] for r in rows], "labels": labels.tolist()})


# Tokenizes a dataset's text field with the base model's tokenizer.
def _tokenize(dataset, tokenizer):
    def _map(batch):
        return tokenizer(batch["text"], truncation=True, max_length=MAX_LENGTH, padding="max_length")

    return dataset.map(_map, batched=True)


# Fine-tunes one fold and returns the trained model plus its eval metrics.
def _train_one_fold(train_rows: list[dict], eval_rows: list[dict], binarizer: MultiLabelBinarizer):
    import numpy as np
    from sklearn.metrics import f1_score, precision_score
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(binarizer.classes_), problem_type="multi_label_classification"
    )

    train_dataset = _tokenize(_build_dataset(train_rows, binarizer), tokenizer)
    eval_dataset = _tokenize(_build_dataset(eval_rows, binarizer), tokenizer)

    def _compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = (1 / (1 + np.exp(-logits)) >= 0.5).astype(int)
        return {
            "macro_precision": precision_score(labels, predictions, average="macro", zero_division=0),
            "macro_f1": f1_score(labels, predictions, average="macro", zero_division=0),
        }

    args = TrainingArguments(
        output_dir=str(CHECKPOINT_DIR / "tmp"),
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        num_train_epochs=NUM_EPOCHS,
        eval_strategy="epoch",
        save_strategy="no",
        report_to="none",
    )
    trainer = Trainer(model=model, args=args, train_dataset=train_dataset, eval_dataset=eval_dataset, compute_metrics=_compute_metrics)
    trainer.train()
    return model, tokenizer, trainer.evaluate()


def main() -> None:
    rows = _load_rows()
    binarizer = MultiLabelBinarizer().fit([r["categories"] for r in rows])
    groups = [r["contract_id"] for r in rows]

    gkf = GroupKFold(n_splits=N_FOLDS)
    fold_metrics = []
    best_model, best_tokenizer = None, None

    for fold_idx, (train_idx, eval_idx) in enumerate(gkf.split(rows, groups=groups)):
        train_rows = [rows[i] for i in train_idx]
        eval_rows = [rows[i] for i in eval_idx]
        model, tokenizer, metrics = _train_one_fold(train_rows, eval_rows, binarizer)
        print(f"Fold {fold_idx}: macro_f1 {metrics['eval_macro_f1']:.3f}, macro_precision {metrics['eval_macro_precision']:.3f}")
        fold_metrics.append(metrics)
        if best_model is None or metrics["eval_macro_f1"] >= max(m["eval_macro_f1"] for m in fold_metrics):
            best_model, best_tokenizer = model, tokenizer

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    best_model.save_pretrained(CHECKPOINT_DIR)
    best_tokenizer.save_pretrained(CHECKPOINT_DIR)
    print(f"Saved best fold's model to {CHECKPOINT_DIR}")
    print("Compare its macro F1 against ml/classify/train.py's baseline before deciding which one ships.")


if __name__ == "__main__":
    main()
