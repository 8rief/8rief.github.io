"""Tiny PyTorch inference-boundary lab.

The lab deliberately uses Dropout and BatchNorm so that `model.eval()` has a
visible effect. The task is a deterministic 2D classifier; the teaching target
is the inference pipeline, not model novelty.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


@dataclass(frozen=True)
class PointExample:
    sample_id: str
    x0: float
    x1: float
    label: int

    def features(self) -> list[float]:
        return [self.x0, self.x1]


@dataclass(frozen=True)
class Batch:
    sample_ids: list[str]
    features: torch.Tensor
    labels: torch.Tensor


class PointDataset(Dataset[PointExample]):
    def __init__(self, examples: Sequence[PointExample]) -> None:
        self.examples = list(examples)

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> PointExample:
        return self.examples[index]


def collate_points(examples: list[PointExample]) -> Batch:
    return Batch(
        sample_ids=[example.sample_id for example in examples],
        features=torch.tensor([example.features() for example in examples], dtype=torch.float32),
        labels=torch.tensor([example.label for example in examples], dtype=torch.long),
    )


def make_examples() -> dict[str, list[PointExample]]:
    examples: list[PointExample] = []
    idx = 0
    # Deterministic grid avoids random data drift and keeps the decision boundary visible.
    for i in range(-12, 13):
        for j in range(-12, 13):
            x0 = i / 6.0
            x1 = j / 6.0
            margin = x0 + 0.75 * x1
            if abs(margin) < 0.12:
                continue
            label = int(margin > 0)
            examples.append(PointExample(sample_id=f"p{idx:04d}", x0=x0, x1=x1, label=label))
            idx += 1
    # Stable stratified split by index modulo; both classes appear in every split.
    splits = {"train": [], "val": [], "test": []}
    for k, example in enumerate(examples):
        bucket = k % 10
        if bucket < 7:
            splits["train"].append(example)
        elif bucket < 8:
            splits["val"].append(example)
        else:
            splits["test"].append(example)
    return splits


def make_loader(examples: Sequence[PointExample], *, batch_size: int, shuffle: bool, seed: int) -> DataLoader[Batch]:
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        PointDataset(examples),
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=collate_points,
        generator=generator,
        num_workers=0,
    )


class InferenceDemoNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.Dropout(p=0.35),
            nn.Linear(16, 2),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


def set_reproducibility(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def majority_baseline_accuracy(train: Sequence[PointExample], test: Sequence[PointExample]) -> float:
    counts = [0, 0]
    for example in train:
        counts[example.label] += 1
    majority = 0 if counts[0] >= counts[1] else 1
    return sum(int(example.label == majority) for example in test) / len(test)


def train_model(train: Sequence[PointExample], val: Sequence[PointExample], *, seed: int = 20260714, epochs: int = 120) -> tuple[InferenceDemoNet, list[dict[str, float]]]:
    set_reproducibility(seed)
    model = InferenceDemoNet()
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.035, weight_decay=0.001)
    train_loader = make_loader(train, batch_size=64, shuffle=True, seed=seed)
    val_loader = make_loader(val, batch_size=128, shuffle=False, seed=seed)
    history: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        for batch in train_loader:
            logits = model(batch.features)
            loss = loss_fn(logits, batch.labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        if epoch in {1, 2, 5, 10, 20, 40, 80, epochs}:
            train_metrics = evaluate(model, train_loader, loss_fn)
            val_metrics = evaluate(model, val_loader, loss_fn)
            history.append(
                {
                    "epoch": float(epoch),
                    "train_loss": float(train_metrics["loss"]),
                    "train_acc": float(train_metrics["accuracy"]),
                    "val_loss": float(val_metrics["loss"]),
                    "val_acc": float(val_metrics["accuracy"]),
                }
            )
    return model, history


def evaluate(model: InferenceDemoNet, loader: DataLoader[Batch], loss_fn: nn.Module) -> dict[str, float]:
    was_training = model.training
    model.eval()
    total_loss = 0.0
    total = 0
    correct = 0
    with torch.inference_mode():
        for batch in loader:
            logits = model(batch.features)
            loss = loss_fn(logits, batch.labels)
            total_loss += float(loss.item()) * int(batch.labels.numel())
            total += int(batch.labels.numel())
            correct += int((logits.argmax(dim=1) == batch.labels).sum().item())
    model.train(was_training)
    return {"loss": total_loss / total, "accuracy": correct / total}


def predict_table(model: InferenceDemoNet, loader: DataLoader[Batch]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    model.eval()
    with torch.inference_mode():
        for batch in loader:
            logits = model(batch.features)
            probs = torch.softmax(logits, dim=1)
            preds = probs.argmax(dim=1)
            for sample_id, feature, gold, pred, prob in zip(batch.sample_ids, batch.features.tolist(), batch.labels.tolist(), preds.tolist(), probs.tolist()):
                rows.append(
                    {
                        "sample_id": sample_id,
                        "x0": feature[0],
                        "x1": feature[1],
                        "gold": int(gold),
                        "pred": int(pred),
                        "prob_1": float(prob[1]),
                    }
                )
    return rows


def check_mode_boundaries(model: InferenceDemoNet, example: PointExample) -> dict[str, Any]:
    features = torch.tensor([example.features()] * 8, dtype=torch.float32)
    model.train()
    torch.manual_seed(11)
    train_logits_a = model(features)
    torch.manual_seed(12)
    train_logits_b = model(features)
    train_changed = not torch.allclose(train_logits_a, train_logits_b)

    model.eval()
    with torch.no_grad():
        eval_logits_a = model(features)
        eval_logits_b = model(features)
    eval_stable = torch.allclose(eval_logits_a, eval_logits_b)

    with torch.inference_mode():
        inference_logits = model(features)
        inference_requires_grad = bool(inference_logits.requires_grad)
        inference_mode_enabled = bool(torch.is_inference_mode_enabled())
    return {
        "train_mode_output_changed": train_changed,
        "eval_output_stable": eval_stable,
        "inference_requires_grad": inference_requires_grad,
        "inference_mode_enabled_inside": inference_mode_enabled,
    }


def compare_single_vs_batch(model: InferenceDemoNet, examples: Sequence[PointExample]) -> dict[str, Any]:
    model.eval()
    batch = collate_points(list(examples))
    with torch.inference_mode():
        batch_logits = model(batch.features)
        single_logits = torch.cat([model(torch.tensor([example.features()], dtype=torch.float32)) for example in examples], dim=0)
    max_diff = float((batch_logits - single_logits).abs().max().item())
    return {"batch_output_match": max_diff < 1e-5, "max_batch_single_diff": max_diff}


def benchmark_inference(model: InferenceDemoNet, examples: Sequence[PointExample], *, repeats: int = 60) -> dict[str, float]:
    model.eval()
    features = torch.tensor([example.features() for example in examples], dtype=torch.float32)
    # Warm up Python, kernels and BatchNorm eval reads before measuring.
    with torch.inference_mode():
        for _ in range(10):
            _ = model(features)
    start = time.perf_counter()
    with torch.inference_mode():
        for _ in range(repeats):
            _ = model(features)
    batch_total = time.perf_counter() - start

    sample_features = [torch.tensor([example.features()], dtype=torch.float32) for example in examples]
    with torch.inference_mode():
        for _ in range(2):
            for feature in sample_features:
                _ = model(feature)
    start = time.perf_counter()
    with torch.inference_mode():
        for _ in range(repeats):
            for feature in sample_features:
                _ = model(feature)
    single_total = time.perf_counter() - start
    sample_count = len(examples) * repeats
    return {
        "batch_total_ms": batch_total * 1000.0,
        "single_total_ms": single_total * 1000.0,
        "batch_per_sample_us": batch_total * 1_000_000.0 / sample_count,
        "single_per_sample_us": single_total * 1_000_000.0 / sample_count,
        "batching_speedup": single_total / batch_total if batch_total > 0 else 0.0,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_history(path: Path, rows: Sequence[dict[str, float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["epoch", "train_loss", "train_acc", "val_loss", "val_acc"])
        writer.writeheader()
        writer.writerows(rows)


def save_predictions(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["sample_id", "x0", "x1", "gold", "pred", "prob_1"])
        writer.writeheader()
        writer.writerows(rows)
