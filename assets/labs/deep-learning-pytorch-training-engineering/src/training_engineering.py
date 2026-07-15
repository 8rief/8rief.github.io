"""Small PyTorch training-engineering lab.

The task is intentionally simple: classify 2D points by the sign of x + y.
The value is in the training wrapper: explicit config hashing, validation,
checkpoint/resume, JSONL events, artifact manifest and a model card.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import torch
from torch import nn


@dataclass(frozen=True)
class DatasetSplit:
    name: str
    features: torch.Tensor
    labels: torch.Tensor
    raw_points: list[tuple[int, int, int]]

    @property
    def size(self) -> int:
        return int(self.labels.numel())


@dataclass(frozen=True)
class TrainConfig:
    seed: int
    device: str
    epochs: int
    checkpoint_epoch: int
    learning_rate: float
    momentum: float
    scheduler_step_size: int
    scheduler_gamma: float
    feature_scale: float
    grid_values: list[int]
    train_per_class: int
    val_per_class: int
    task_name: str


def read_config(path: Path) -> TrainConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "seed",
        "device",
        "epochs",
        "checkpoint_epoch",
        "learning_rate",
        "momentum",
        "scheduler_step_size",
        "scheduler_gamma",
        "feature_scale",
        "grid_values",
        "train_per_class",
        "val_per_class",
        "task_name",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"missing config keys: {missing}")
    if data["epochs"] <= data["checkpoint_epoch"]:
        raise ValueError("epochs must be greater than checkpoint_epoch")
    if data["train_per_class"] <= 0 or data["val_per_class"] <= 0:
        raise ValueError("train_per_class and val_per_class must be positive")
    if data["feature_scale"] <= 0:
        raise ValueError("feature_scale must be positive")
    return TrainConfig(**data)


def config_to_dict(config: TrainConfig) -> dict[str, Any]:
    return {
        "seed": config.seed,
        "device": config.device,
        "epochs": config.epochs,
        "checkpoint_epoch": config.checkpoint_epoch,
        "learning_rate": config.learning_rate,
        "momentum": config.momentum,
        "scheduler_step_size": config.scheduler_step_size,
        "scheduler_gamma": config.scheduler_gamma,
        "feature_scale": config.feature_scale,
        "grid_values": list(config.grid_values),
        "train_per_class": config.train_per_class,
        "val_per_class": config.val_per_class,
        "task_name": config.task_name,
    }


def stable_config_json(config: TrainConfig) -> str:
    return json.dumps(config_to_dict(config), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def config_hash(config: TrainConfig) -> str:
    return hashlib.sha256(stable_config_json(config).encode("utf-8")).hexdigest()


def set_reproducibility(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def _sorted_points(values: Iterable[int]) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]]]:
    positives: list[tuple[int, int, int]] = []
    negatives: list[tuple[int, int, int]] = []
    for x in values:
        for y in values:
            if x + y == 0:
                continue
            label = 1 if x + y > 0 else 0
            point = (int(x), int(y), label)
            if label:
                positives.append(point)
            else:
                negatives.append(point)
    key = lambda item: (abs(item[0]) + abs(item[1]), item[0], item[1])
    return sorted(positives, key=key), sorted(negatives, key=key)


def build_splits(config: TrainConfig) -> dict[str, DatasetSplit]:
    positives, negatives = _sorted_points(config.grid_values)
    train_n = config.train_per_class
    val_n = config.val_per_class
    required = train_n + val_n + 1
    if len(positives) < required or len(negatives) < required:
        raise ValueError("grid does not contain enough balanced samples for the requested splits")

    split_points = {
        "train": positives[:train_n] + negatives[:train_n],
        "val": positives[train_n : train_n + val_n] + negatives[train_n : train_n + val_n],
        "test": positives[train_n + val_n :] + negatives[train_n + val_n :],
    }
    return {name: _make_split(name, points, config.feature_scale) for name, points in split_points.items()}


def _make_split(name: str, points: list[tuple[int, int, int]], feature_scale: float) -> DatasetSplit:
    features = torch.tensor([(x / feature_scale, y / feature_scale) for x, y, _ in points], dtype=torch.float32)
    labels = torch.tensor([label for _, _, label in points], dtype=torch.long)
    return DatasetSplit(name=name, features=features, labels=labels, raw_points=points)


def majority_baseline_accuracy(split: DatasetSplit) -> float:
    ones = int(split.labels.sum().item())
    zeros = split.size - ones
    return max(ones, zeros) / split.size


def x_only_heuristic_accuracy(split: DatasetSplit) -> float:
    predictions = (split.features[:, 0] > 0).long()
    return float((predictions == split.labels).float().mean().item())


class TinyLinearClassifier(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.classifier = nn.Linear(2, 2)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.classifier(features)


def make_training_objects(config: TrainConfig) -> tuple[TinyLinearClassifier, torch.optim.Optimizer, torch.optim.lr_scheduler.LRScheduler, nn.Module]:
    model = TinyLinearClassifier()
    optimizer = torch.optim.SGD(model.parameters(), lr=config.learning_rate, momentum=config.momentum)
    scheduler = torch.optim.lr_scheduler.StepLR(
        optimizer,
        step_size=config.scheduler_step_size,
        gamma=config.scheduler_gamma,
    )
    loss_fn = nn.CrossEntropyLoss()
    return model, optimizer, scheduler, loss_fn


def evaluate(model: nn.Module, split: DatasetSplit, loss_fn: nn.Module) -> dict[str, float]:
    model.eval()
    with torch.no_grad():
        logits = model(split.features)
        loss = float(loss_fn(logits, split.labels).item())
        accuracy = float((logits.argmax(dim=1) == split.labels).float().mean().item())
    return {"loss": loss, "accuracy": accuracy}


def predict_logits(model: nn.Module, split: DatasetSplit) -> torch.Tensor:
    model.eval()
    with torch.no_grad():
        return model(split.features).detach().cpu()


def train_one_epoch(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    loss_fn: nn.Module,
    train_split: DatasetSplit,
) -> float:
    model.train()
    optimizer.zero_grad(set_to_none=True)
    logits = model(train_split.features)
    loss = loss_fn(logits, train_split.labels)
    loss.backward()
    optimizer.step()
    scheduler.step()
    return float(loss.item())


def checkpoint_payload(
    *,
    epoch: int,
    config: TrainConfig,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    metrics: dict[str, Any],
    test_logits: torch.Tensor,
) -> dict[str, Any]:
    return {
        "epoch": int(epoch),
        "config": config_to_dict(config),
        "config_hash": config_hash(config),
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "torch_rng_state": torch.get_rng_state(),
        "metrics": metrics,
        "test_logits": test_logits,
    }


def save_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)


def load_checkpoint(path: Path, config: TrainConfig) -> tuple[TinyLinearClassifier, torch.optim.Optimizer, torch.optim.lr_scheduler.LRScheduler, nn.Module, int, dict[str, Any]]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    if checkpoint.get("config_hash") != config_hash(config):
        raise ValueError("checkpoint config hash does not match current config")
    model, optimizer, scheduler, loss_fn = make_training_objects(config)
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
    torch.set_rng_state(checkpoint["torch_rng_state"])
    return model, optimizer, scheduler, loss_fn, int(checkpoint["epoch"]), checkpoint


def run_training(
    *,
    config: TrainConfig,
    splits: dict[str, DatasetSplit],
    reports_dir: Path,
    run_id: str,
    resume_checkpoint: Path | None = None,
) -> dict[str, Any]:
    events_path = reports_dir / f"{run_id}_events.jsonl"
    checkpoints_dir = reports_dir / "checkpoints"
    best_path = checkpoints_dir / "best.pt"
    full_checkpoint_path = checkpoints_dir / f"{run_id}_epoch_{config.checkpoint_epoch:03d}.pt"
    final_path = checkpoints_dir / f"{run_id}_final.pt"

    if resume_checkpoint is None:
        set_reproducibility(config.seed)
        model, optimizer, scheduler, loss_fn = make_training_objects(config)
        start_epoch = 0
        best_metric: tuple[float, float, int] | None = None
    else:
        model, optimizer, scheduler, loss_fn, start_epoch, checkpoint = load_checkpoint(resume_checkpoint, config)
        best_metric = checkpoint.get("best_metric")

    events: list[dict[str, Any]] = []
    reports_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(start_epoch + 1, config.epochs + 1):
        train_loss = train_one_epoch(model, optimizer, scheduler, loss_fn, splits["train"])
        metrics = {
            "train": evaluate(model, splits["train"], loss_fn),
            "val": evaluate(model, splits["val"], loss_fn),
            "test": evaluate(model, splits["test"], loss_fn),
        }
        event = {
            "run_id": run_id,
            "epoch": epoch,
            "train_loss_before_eval": train_loss,
            "train_accuracy": metrics["train"]["accuracy"],
            "val_accuracy": metrics["val"]["accuracy"],
            "test_accuracy": metrics["test"]["accuracy"],
            "val_loss": metrics["val"]["loss"],
            "learning_rate": float(optimizer.param_groups[0]["lr"]),
            "config_hash": config_hash(config),
        }
        events.append(event)
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

        current_rank = (metrics["val"]["accuracy"], -metrics["val"]["loss"], -epoch)
        if best_metric is None or current_rank > tuple(best_metric):
            best_metric = current_rank
            payload = checkpoint_payload(
                epoch=epoch,
                config=config,
                model=model,
                optimizer=optimizer,
                scheduler=scheduler,
                metrics=metrics,
                test_logits=predict_logits(model, splits["test"]),
            )
            payload["best_metric"] = list(best_metric)
            save_checkpoint(best_path, payload)

        if resume_checkpoint is None and epoch == config.checkpoint_epoch:
            payload = checkpoint_payload(
                epoch=epoch,
                config=config,
                model=model,
                optimizer=optimizer,
                scheduler=scheduler,
                metrics=metrics,
                test_logits=predict_logits(model, splits["test"]),
            )
            payload["best_metric"] = list(best_metric) if best_metric is not None else None
            save_checkpoint(full_checkpoint_path, payload)

    final_metrics = {
        "train": evaluate(model, splits["train"], loss_fn),
        "val": evaluate(model, splits["val"], loss_fn),
        "test": evaluate(model, splits["test"], loss_fn),
    }
    final_payload = checkpoint_payload(
        epoch=config.epochs,
        config=config,
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        metrics=final_metrics,
        test_logits=predict_logits(model, splits["test"]),
    )
    final_payload["best_metric"] = list(best_metric) if best_metric is not None else None
    save_checkpoint(final_path, final_payload)
    return {
        "run_id": run_id,
        "events_path": str(events_path),
        "checkpoint_epoch_path": str(full_checkpoint_path) if resume_checkpoint is None else None,
        "best_path": str(best_path),
        "final_path": str(final_path),
        "final_metrics": final_metrics,
        "events": events,
    }


def state_dicts_allclose(left_path: Path, right_path: Path) -> bool:
    left = torch.load(left_path, map_location="cpu", weights_only=True)
    right = torch.load(right_path, map_location="cpu", weights_only=True)
    for key, left_tensor in left["model_state_dict"].items():
        right_tensor = right["model_state_dict"][key]
        if not torch.equal(left_tensor, right_tensor):
            return False
    return True


def checkpoint_logits_match(path: Path, config: TrainConfig, split: DatasetSplit) -> bool:
    model, _optimizer, _scheduler, _loss_fn, _epoch, checkpoint = load_checkpoint(path, config)
    current_logits = predict_logits(model, split)
    saved_logits = checkpoint["test_logits"]
    return bool(torch.equal(current_logits, saved_logits))


def write_prediction_table(path: Path, model: nn.Module, split: DatasetSplit) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    logits = predict_logits(model, split)
    predictions = logits.argmax(dim=1)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["split", "x", "y", "label", "pred", "logit_0", "logit_1"])
        for (x, y, label), pred, row in zip(split.raw_points, predictions.tolist(), logits.tolist()):
            writer.writerow([split.name, x, y, label, pred, f"{row[0]:.6f}", f"{row[1]:.6f}"])


def write_model_card(path: Path, *, config: TrainConfig, summary: dict[str, Any]) -> None:
    text = f"""# Tiny PyTorch classifier model card

## Intended use

This model is a teaching artifact for a synthetic two-dimensional classification task. It demonstrates a reproducible PyTorch training wrapper rather than a useful real-world classifier.

## Task

A sample is a point `(x, y)`. The label is `1` when `x + y > 0` and `0` when `x + y < 0`. Points with `x + y = 0` are excluded so the boundary is unambiguous.

## Data and split

- Train samples: {summary['train_samples']}
- Validation samples: {summary['val_samples']}
- Test samples: {summary['test_samples']}
- Config hash: `{config_hash(config)}`

## Metrics

- Majority baseline test accuracy: {summary['majority_baseline_acc']:.3f}
- x-only heuristic test accuracy: {summary['heuristic_baseline_acc']:.3f}
- Final validation accuracy: {summary['final_val_acc']:.3f}
- Final test accuracy: {summary['final_test_acc']:.3f}

## Limitations

The task is linearly separable and tiny. Passing this lab shows that config, validation, checkpoint/reload and resume are wired correctly. It does not show robustness on natural data, GPU scaling, mixed precision behavior, or production monitoring quality.
"""
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_artifact_manifest(path: Path, root: Path, include_globs: Iterable[str]) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    for pattern in include_globs:
        for item in sorted(root.glob(pattern)):
            if item.is_file():
                artifacts.append(
                    {
                        "path": item.relative_to(root).as_posix(),
                        "bytes": item.stat().st_size,
                        "sha256": sha256_file(item),
                    }
                )
    manifest = {"artifact_count": len(artifacts), "artifacts": artifacts}
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def reset_reports_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def format_marker(name: str, value: Any) -> str:
    if isinstance(value, float):
        return f"{name}={value:.3f}"
    return f"{name}={value}"
