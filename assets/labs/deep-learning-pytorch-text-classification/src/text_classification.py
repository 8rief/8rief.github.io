"""Minimal PyTorch text-classification project for a teaching lab.

The model is deliberately small. The goal is to expose the data pipeline:
text -> tokens -> ids -> padded mini-batch -> mask-aware mean embedding -> logits.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import torch
from torch import nn
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset

PAD = "<pad>"
UNK = "<unk>"
LABELS = ["billing", "shipping", "tech"]
LABEL_TO_ID = {label: idx for idx, label in enumerate(LABELS)}
TOKEN_RE = re.compile(r"[a-z0-9]+")

CLASS_KEYWORDS: dict[str, list[str]] = {
    "billing": ["invoice", "refund", "charge", "payment", "receipt", "billing"],
    "shipping": ["delivery", "tracking", "package", "address", "courier", "shipping"],
    "tech": ["login", "password", "error", "server", "crash", "technical"],
}

NEUTRAL_PHRASES = [
    "please help with",
    "my account shows",
    "urgent question about",
    "can you check the",
    "i need support for",
    "the customer reported",
]

TAILS = [
    "today",
    "after the update",
    "before noon",
    "on the mobile app",
    "for my team",
    "with the latest request",
]


@dataclass(frozen=True)
class TextExample:
    text: str
    label: int

    @property
    def label_name(self) -> str:
        return LABELS[self.label]


@dataclass(frozen=True)
class Batch:
    input_ids: torch.Tensor
    labels: torch.Tensor
    lengths: torch.Tensor
    texts: list[str]


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def build_examples() -> dict[str, list[TextExample]]:
    examples_by_label: dict[str, list[TextExample]] = {label: [] for label in LABELS}
    for label in LABELS:
        keywords = CLASS_KEYWORDS[label]
        for idx, keyword in enumerate(keywords):
            examples_by_label[label].append(
                TextExample(f"{NEUTRAL_PHRASES[idx % len(NEUTRAL_PHRASES)]} {keyword} {TAILS[idx % len(TAILS)]}", LABEL_TO_ID[label])
            )
            examples_by_label[label].append(
                TextExample(f"{TAILS[(idx + 2) % len(TAILS)]} {keyword} {NEUTRAL_PHRASES[(idx + 3) % len(NEUTRAL_PHRASES)]}", LABEL_TO_ID[label])
            )
            examples_by_label[label].append(
                TextExample(f"{NEUTRAL_PHRASES[(idx + 4) % len(NEUTRAL_PHRASES)]} {TAILS[(idx + 1) % len(TAILS)]} {keyword}", LABEL_TO_ID[label])
            )
    return examples_by_label


def split_examples() -> dict[str, list[TextExample]]:
    by_label = build_examples()
    splits = {"train": [], "val": [], "test": []}
    for label in LABELS:
        items = by_label[label]
        # 18 examples per class: each keyword contributes three templates.
        # Train keeps two examples for every keyword, so the vocabulary covers
        # the class cues. Validation/test receive held-out phrasings, not wholly
        # unseen labels.
        for keyword_index in range(6):
            group = items[3 * keyword_index : 3 * keyword_index + 3]
            splits["train"].extend(group[:2])
            if keyword_index < 3:
                splits["val"].append(group[2])
            else:
                splits["test"].append(group[2])
    return splits


def build_vocab(examples: Iterable[TextExample]) -> dict[str, int]:
    tokens = sorted({token for example in examples for token in tokenize(example.text)})
    vocab = {PAD: 0, UNK: 1}
    for token in tokens:
        if token not in vocab:
            vocab[token] = len(vocab)
    return vocab


def encode(text: str, vocab: dict[str, int]) -> list[int]:
    return [vocab.get(token, vocab[UNK]) for token in tokenize(text)] or [vocab[UNK]]


class TicketDataset(Dataset[TextExample]):
    def __init__(self, examples: Sequence[TextExample]) -> None:
        self.examples = list(examples)

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> TextExample:
        return self.examples[index]


def make_collate_fn(vocab: dict[str, int]):
    pad_id = vocab[PAD]

    def collate(examples: list[TextExample]) -> Batch:
        encoded = [torch.tensor(encode(example.text, vocab), dtype=torch.long) for example in examples]
        lengths = torch.tensor([len(item) for item in encoded], dtype=torch.long)
        input_ids = pad_sequence(encoded, batch_first=True, padding_value=pad_id)
        labels = torch.tensor([example.label for example in examples], dtype=torch.long)
        return Batch(input_ids=input_ids, labels=labels, lengths=lengths, texts=[example.text for example in examples])

    return collate


def make_loader(examples: Sequence[TextExample], vocab: dict[str, int], *, batch_size: int, shuffle: bool, seed: int) -> DataLoader[Batch]:
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        TicketDataset(examples),
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=make_collate_fn(vocab),
        generator=generator,
        num_workers=0,
    )


class MeanEmbeddingClassifier(nn.Module):
    def __init__(self, vocab_size: int, embedding_dim: int, num_labels: int, pad_id: int) -> None:
        super().__init__()
        self.pad_id = pad_id
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_id)
        self.classifier = nn.Linear(embedding_dim, num_labels)

    def forward(self, input_ids: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(input_ids)
        mask = input_ids.ne(self.pad_id).unsqueeze(-1)
        summed = (embedded * mask).sum(dim=1)
        denom = lengths.clamp_min(1).to(embedded.dtype).unsqueeze(-1)
        pooled = summed / denom
        return self.classifier(pooled)


def set_reproducibility(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def majority_baseline(examples: Sequence[TextExample]) -> float:
    counts = [0 for _ in LABELS]
    for example in examples:
        counts[example.label] += 1
    return max(counts) / len(examples)


def first_token_baseline(train: Sequence[TextExample], test: Sequence[TextExample]) -> float:
    token_counts: dict[str, list[int]] = {}
    label_counts = [0 for _ in LABELS]
    for example in train:
        label_counts[example.label] += 1
        token = tokenize(example.text)[0]
        token_counts.setdefault(token, [0 for _ in LABELS])[example.label] += 1
    default_label = max(range(len(LABELS)), key=lambda i: (label_counts[i], -i))
    token_to_label = {token: max(range(len(LABELS)), key=lambda i: (counts[i], -i)) for token, counts in token_counts.items()}
    correct = 0
    for example in test:
        token = tokenize(example.text)[0]
        pred = token_to_label.get(token, default_label)
        correct += int(pred == example.label)
    return correct / len(test)


def keyword_rule_baseline(examples: Sequence[TextExample]) -> float:
    keyword_to_label = {keyword: label for label, words in CLASS_KEYWORDS.items() for keyword in words}
    correct = 0
    for example in examples:
        tokens = tokenize(example.text)
        pred_name = next((keyword_to_label[token] for token in tokens if token in keyword_to_label), "billing")
        correct += int(LABEL_TO_ID[pred_name] == example.label)
    return correct / len(examples)


def evaluate(model: MeanEmbeddingClassifier, loader: DataLoader[Batch], loss_fn: nn.Module) -> dict[str, Any]:
    model.eval()
    total_loss = 0.0
    total = 0
    correct = 0
    confusion = [[0 for _ in LABELS] for _ in LABELS]
    predictions: list[dict[str, Any]] = []
    with torch.no_grad():
        for batch in loader:
            logits = model(batch.input_ids, batch.lengths)
            loss = loss_fn(logits, batch.labels)
            preds = logits.argmax(dim=1)
            total_loss += float(loss.item()) * int(batch.labels.numel())
            total += int(batch.labels.numel())
            correct += int((preds == batch.labels).sum().item())
            for text, gold, pred, row in zip(batch.texts, batch.labels.tolist(), preds.tolist(), logits.tolist()):
                confusion[gold][pred] += 1
                predictions.append(
                    {
                        "text": text,
                        "gold": LABELS[gold],
                        "pred": LABELS[pred],
                        "logits": [float(value) for value in row],
                    }
                )
    return {"loss": total_loss / total, "accuracy": correct / total, "confusion": confusion, "predictions": predictions}


def train_model(
    train: Sequence[TextExample],
    val: Sequence[TextExample],
    vocab: dict[str, int],
    *,
    seed: int = 20260713,
    epochs: int = 18,
    batch_size: int = 9,
) -> tuple[MeanEmbeddingClassifier, list[dict[str, float]]]:
    set_reproducibility(seed)
    model = MeanEmbeddingClassifier(vocab_size=len(vocab), embedding_dim=16, num_labels=len(LABELS), pad_id=vocab[PAD])
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.08, weight_decay=0.0)
    train_loader = make_loader(train, vocab, batch_size=batch_size, shuffle=True, seed=seed)
    val_loader = make_loader(val, vocab, batch_size=batch_size, shuffle=False, seed=seed)
    history: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        for batch in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch.input_ids, batch.lengths)
            loss = loss_fn(logits, batch.labels)
            loss.backward()
            optimizer.step()
        train_metrics = evaluate(model, train_loader, loss_fn)
        val_metrics = evaluate(model, val_loader, loss_fn)
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": float(train_metrics["loss"]),
                "train_accuracy": float(train_metrics["accuracy"]),
                "val_loss": float(val_metrics["loss"]),
                "val_accuracy": float(val_metrics["accuracy"]),
            }
        )
    return model, history


def checkpoint_payload(model: MeanEmbeddingClassifier, vocab: dict[str, int], history: list[dict[str, float]], metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "model_state_dict": model.state_dict(),
        "vocab": vocab,
        "labels": LABELS,
        "history": history,
        "metrics": {"loss": metrics["loss"], "accuracy": metrics["accuracy"], "confusion": metrics["confusion"]},
    }


def reload_checkpoint(path: Path) -> tuple[MeanEmbeddingClassifier, dict[str, int], dict[str, Any]]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    vocab = checkpoint["vocab"]
    model = MeanEmbeddingClassifier(vocab_size=len(vocab), embedding_dim=16, num_labels=len(LABELS), pad_id=vocab[PAD])
    model.load_state_dict(checkpoint["model_state_dict"])
    return model, vocab, checkpoint


def tensor_sha256(tensor: torch.Tensor) -> str:
    arr = tensor.detach().cpu().contiguous().numpy().tobytes()
    return hashlib.sha256(arr).hexdigest()


def write_history(path: Path, history: list[dict[str, float]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["epoch", "train_loss", "train_accuracy", "val_loss", "val_accuracy"])
        writer.writeheader()
        for row in history:
            writer.writerow(row)


def write_confusion(path: Path, confusion: list[list[int]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gold\\pred", *LABELS])
        for label, row in zip(LABELS, confusion):
            writer.writerow([label, *row])


def write_predictions(path: Path, predictions: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["text", "gold", "pred", "logit_billing", "logit_shipping", "logit_tech"])
        for row in predictions:
            writer.writerow([row["text"], row["gold"], row["pred"], *[f"{v:.6f}" for v in row["logits"]]])


def write_report(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# PyTorch text classification report

## Task

Classify short support-ticket messages into billing, shipping or tech categories.

## Split and vocabulary

- Train samples: {summary['train_samples']}
- Validation samples: {summary['val_samples']}
- Test samples: {summary['test_samples']}
- Vocabulary size: {summary['vocab_size']}
- Maximum padded batch width: {summary['max_batch_width']}

## Baselines and model

- Majority baseline: {summary['majority_baseline_acc']:.3f}
- First-token baseline: {summary['first_token_baseline_acc']:.3f}
- Keyword-rule baseline: {summary['keyword_rule_baseline_acc']:.3f}
- Model validation accuracy: {summary['model_val_acc']:.3f}
- Model test accuracy: {summary['model_test_acc']:.3f}

## Boundary

The dataset is synthetic and deliberately keyword-driven. A transparent keyword rule already solves it. The neural model is included to teach the PyTorch text pipeline, not to claim superiority over rules on this toy task.
"""
    path.write_text(text, encoding="utf-8")


def max_batch_stats(loader: DataLoader[Batch], pad_id: int) -> tuple[tuple[int, int], int]:
    max_shape = (0, 0)
    pad_count = 0
    for batch in loader:
        shape = tuple(batch.input_ids.shape)
        max_shape = max(max_shape, shape, key=lambda item: item[1])
        pad_count += int(batch.input_ids.eq(pad_id).sum().item())
    return max_shape, pad_count
