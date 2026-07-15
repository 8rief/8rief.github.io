from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from .data import DatasetBundle, make_xor_gaussians
from .models import build_model


@dataclass(frozen=True)
class Metrics:
    model: str
    split: str
    loss: float
    accuracy: float
    positive_rate: float
    examples: int


@dataclass(frozen=True)
class TrainingResult:
    model: str
    epochs: int
    learning_rate: float
    train: Metrics
    val: Metrics
    test: Metrics
    checkpoint: str
    history_csv: str


def set_reproducible(seed: int = 20260625) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


def logits_to_predictions(logits: torch.Tensor) -> torch.Tensor:
    return (torch.sigmoid(logits) >= 0.5).to(torch.float32)


def binary_accuracy(logits: torch.Tensor, y: torch.Tensor) -> float:
    return float((logits_to_predictions(logits) == y).to(torch.float32).mean().item())


def evaluate_model(model: nn.Module, bundle: DatasetBundle, split: str, loss_fn: nn.Module) -> Metrics:
    x, y = bundle.split(split)
    model.eval()
    with torch.no_grad():
        logits = model(x)
        loss = float(loss_fn(logits, y).item())
        acc = binary_accuracy(logits, y)
    return Metrics(
        model=model.__class__.__name__,
        split=split,
        loss=loss,
        accuracy=acc,
        positive_rate=float(y.mean().item()),
        examples=int(y.numel()),
    )


def majority_baseline(bundle: DatasetBundle, output_dir: Path) -> Metrics:
    output_dir.mkdir(parents=True, exist_ok=True)
    majority = float(bundle.train_y.mean().item() >= 0.5)
    test_logits = torch.full_like(bundle.test_y, 12.0 if majority else -12.0)
    loss_fn = nn.BCEWithLogitsLoss()
    metrics = Metrics(
        model="MajorityBaseline",
        split="test",
        loss=float(loss_fn(test_logits, bundle.test_y).item()),
        accuracy=binary_accuracy(test_logits, bundle.test_y),
        positive_rate=float(bundle.test_y.mean().item()),
        examples=int(bundle.test_y.numel()),
    )
    write_json(output_dir / "metrics.json", asdict(metrics) | {"majority_class": majority})
    return metrics


def train_model(
    model_name: str,
    output_dir: Path,
    epochs: int = 200,
    learning_rate: float = 0.03,
    batch_size: int = 64,
    seed: int = 20260625,
) -> TrainingResult:
    set_reproducible(seed)
    bundle = make_xor_gaussians(seed=seed)
    model = build_model(model_name)
    loss_fn = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(
        bundle.as_dataset("train"), batch_size=batch_size, shuffle=True, generator=generator
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, float | int | str]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        for batch_x, batch_y in loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch_x)
            loss = loss_fn(logits, batch_y)
            loss.backward()
            optimizer.step()

        train_metrics = evaluate_model(model, bundle, "train", loss_fn)
        val_metrics = evaluate_model(model, bundle, "val", loss_fn)
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_metrics.loss,
                "train_accuracy": train_metrics.accuracy,
                "val_loss": val_metrics.loss,
                "val_accuracy": val_metrics.accuracy,
            }
        )

    train_metrics = evaluate_model(model, bundle, "train", loss_fn)
    val_metrics = evaluate_model(model, bundle, "val", loss_fn)
    test_metrics = evaluate_model(model, bundle, "test", loss_fn)
    history_csv = output_dir / "history.csv"
    write_history_csv(history_csv, history)
    checkpoint_path = output_dir / "checkpoint.pt"
    torch.save(
        {
            "model_name": model_name,
            "model_state_dict": model.state_dict(),
            "seed": seed,
            "epochs": epochs,
            "learning_rate": learning_rate,
            "test_accuracy": test_metrics.accuracy,
        },
        checkpoint_path,
    )
    result = TrainingResult(
        model=model_name,
        epochs=epochs,
        learning_rate=learning_rate,
        train=train_metrics,
        val=val_metrics,
        test=test_metrics,
        checkpoint=str(checkpoint_path),
        history_csv=str(history_csv),
    )
    write_json(output_dir / "metrics.json", result_to_dict(result))
    return result


def result_to_dict(result: TrainingResult) -> dict[str, object]:
    data = asdict(result)
    return data


def load_checkpoint_accuracy(checkpoint_path: Path, split: str = "test", seed: int = 20260625) -> float:
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model = build_model(str(state["model_name"]))
    model.load_state_dict(state["model_state_dict"])
    bundle = make_xor_gaussians(seed=seed)
    metrics = evaluate_model(model, bundle, split, nn.BCEWithLogitsLoss())
    return metrics.accuracy


def tensor_demo() -> dict[str, object]:
    x = torch.arange(12, dtype=torch.float32).reshape(3, 4)
    scale = torch.tensor([1.0, 10.0, 100.0, 1000.0])
    broadcast = x * scale
    batch = torch.arange(24, dtype=torch.float32).reshape(2, 3, 4)
    weights = torch.ones((4, 2), dtype=torch.float32)
    logits = batch @ weights
    return {
        "x_shape": list(x.shape),
        "x_dtype": str(x.dtype),
        "broadcast_shape": list(broadcast.shape),
        "broadcast_first_row": broadcast[0].tolist(),
        "batch_shape": list(batch.shape),
        "weights_shape": list(weights.shape),
        "logits_shape": list(logits.shape),
    }


def autograd_demo(eps: float = 1e-3) -> dict[str, object]:
    x = torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=torch.float32)
    y = torch.tensor([1.0, 0.0], dtype=torch.float32)
    w = torch.tensor([0.2, -0.4], dtype=torch.float32, requires_grad=True)

    def loss_for(weight: torch.Tensor) -> torch.Tensor:
        pred = x @ weight
        return torch.mean((pred - y) ** 2)

    loss = loss_for(w)
    loss.backward()
    autograd_grad = w.grad.detach().clone()
    analytic_grad = (2.0 / x.shape[0]) * x.T @ ((x @ w.detach()) - y)
    finite_diffs = []
    base = w.detach().clone()
    for i in range(base.numel()):
        plus = base.clone(); plus[i] += eps
        minus = base.clone(); minus[i] -= eps
        finite_diffs.append(float(((loss_for(plus) - loss_for(minus)) / (2 * eps)).item()))
    finite_tensor = torch.tensor(finite_diffs)
    return {
        "loss": float(loss.item()),
        "autograd_grad": autograd_grad.tolist(),
        "analytic_grad": analytic_grad.tolist(),
        "finite_difference_grad": finite_tensor.tolist(),
        "max_abs_error_vs_finite_difference": float(torch.max(torch.abs(autograd_grad - finite_tensor)).item()),
    }


def compare_metrics(linear_path: Path, mlp_path: Path, majority_path: Path, output_path: Path) -> dict[str, object]:
    majority = json.loads(majority_path.read_text(encoding="utf-8"))
    linear = json.loads(linear_path.read_text(encoding="utf-8"))
    mlp = json.loads(mlp_path.read_text(encoding="utf-8"))
    comparison = {
        "majority_test_accuracy": majority["accuracy"],
        "linear_test_accuracy": linear["test"]["accuracy"],
        "mlp_test_accuracy": mlp["test"]["accuracy"],
        "mlp_minus_linear_accuracy": mlp["test"]["accuracy"] - linear["test"]["accuracy"],
        "claim_boundary": "Synthetic local XOR-style dataset; comparison is a teaching baseline, not a real-world benchmark.",
    }
    write_json(output_path, comparison)
    return comparison


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_history_csv(path: Path, rows: Iterable[dict[str, float | int | str]]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError("history is empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
