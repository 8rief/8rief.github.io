#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

import numpy as np


@dataclass
class Split:
    x: np.ndarray
    y: np.ndarray


def make_spiral(n_per_class: int = 500, noise: float = 0.12, seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    for cls in range(2):
        r = np.linspace(0.05, 1.0, n_per_class)
        theta = cls * np.pi + 6.0 * r + rng.normal(0.0, noise, n_per_class)
        x = np.column_stack([r * np.sin(theta), r * np.cos(theta)])
        xs.append(x)
        ys.append(np.full(n_per_class, cls, dtype=np.int64))
    x_all = np.vstack(xs).astype(np.float64)
    y_all = np.concatenate(ys)
    order = rng.permutation(len(y_all))
    return x_all[order], y_all[order]


def split_and_standardize(x: np.ndarray, y: np.ndarray) -> dict[str, Split | dict[str, list[float]]]:
    train_n = int(0.6 * len(y))
    val_n = int(0.2 * len(y))
    raw = {
        "train": Split(x[:train_n], y[:train_n]),
        "val": Split(x[train_n:train_n + val_n], y[train_n:train_n + val_n]),
        "test": Split(x[train_n + val_n:], y[train_n + val_n:]),
    }
    mean = raw["train"].x.mean(axis=0)
    std = raw["train"].x.std(axis=0) + 1e-8
    out: dict[str, Split | dict[str, list[float]]] = {"normalization": {"mean": mean.tolist(), "std": std.tolist()}}
    for name, split in raw.items():
        out[name] = Split((split.x - mean) / std, split.y)
    return out


def one_hot(y: np.ndarray, classes: int = 2) -> np.ndarray:
    result = np.zeros((len(y), classes), dtype=np.float64)
    result[np.arange(len(y)), y] = 1.0
    return result


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def cross_entropy(probs: np.ndarray, y: np.ndarray) -> float:
    eps = 1e-12
    return float(-np.log(probs[np.arange(len(y)), y] + eps).mean())


def accuracy(probs: np.ndarray, y: np.ndarray) -> float:
    return float((probs.argmax(axis=1) == y).mean())


def train_majority(train: Split) -> int:
    counts = np.bincount(train.y, minlength=2)
    return int(counts.argmax())


def eval_majority(label: int, split: Split) -> dict[str, float]:
    pred = np.full_like(split.y, label)
    return {"accuracy": float((pred == split.y).mean()), "loss": float("nan")}


def init_linear(rng: np.random.Generator) -> dict[str, np.ndarray]:
    return {"W": rng.normal(0, 0.05, (2, 2)), "b": np.zeros(2)}


def linear_logits(params: dict[str, np.ndarray], x: np.ndarray) -> np.ndarray:
    return x @ params["W"] + params["b"]


def train_linear(train: Split, val: Split, epochs: int = 800, lr: float = 0.4, weight_decay: float = 1e-3, seed: int = 11) -> tuple[dict[str, np.ndarray], list[dict[str, float]]]:
    rng = np.random.default_rng(seed)
    params = init_linear(rng)
    y_one = one_hot(train.y)
    history: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        logits = linear_logits(params, train.x)
        probs = softmax(logits)
        diff = (probs - y_one) / len(train.y)
        grad_w = train.x.T @ diff + weight_decay * params["W"]
        grad_b = diff.sum(axis=0)
        params["W"] -= lr * grad_w
        params["b"] -= lr * grad_b
        if epoch == 1 or epoch % 100 == 0 or epoch == epochs:
            history.append({
                "epoch": epoch,
                "train_loss": cross_entropy(softmax(linear_logits(params, train.x)), train.y),
                "train_acc": accuracy(softmax(linear_logits(params, train.x)), train.y),
                "val_acc": accuracy(softmax(linear_logits(params, val.x)), val.y),
            })
    return params, history


def init_mlp(rng: np.random.Generator, hidden: int = 24) -> dict[str, np.ndarray]:
    return {
        "W1": rng.normal(0, 0.7, (2, hidden)),
        "b1": np.zeros(hidden),
        "W2": rng.normal(0, 0.4, (hidden, 2)),
        "b2": np.zeros(2),
    }


def mlp_forward(params: dict[str, np.ndarray], x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    hidden = np.tanh(x @ params["W1"] + params["b1"])
    logits = hidden @ params["W2"] + params["b2"]
    return hidden, logits


def mlp_loss_and_grads(params: dict[str, np.ndarray], split: Split, weight_decay: float = 1e-4) -> tuple[float, dict[str, np.ndarray]]:
    hidden, logits = mlp_forward(params, split.x)
    probs = softmax(logits)
    loss = cross_entropy(probs, split.y) + 0.5 * weight_decay * (np.sum(params["W1"] ** 2) + np.sum(params["W2"] ** 2))
    diff = (probs - one_hot(split.y)) / len(split.y)
    grad_w2 = hidden.T @ diff + weight_decay * params["W2"]
    grad_b2 = diff.sum(axis=0)
    grad_hidden = diff @ params["W2"].T
    grad_z1 = grad_hidden * (1 - hidden ** 2)
    grad_w1 = split.x.T @ grad_z1 + weight_decay * params["W1"]
    grad_b1 = grad_z1.sum(axis=0)
    return float(loss), {"W1": grad_w1, "b1": grad_b1, "W2": grad_w2, "b2": grad_b2}


def train_mlp(train: Split, val: Split, epochs: int = 1800, lr: float = 0.7, seed: int = 13) -> tuple[dict[str, np.ndarray], list[dict[str, float]]]:
    rng = np.random.default_rng(seed)
    params = init_mlp(rng)
    history: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        _, grads = mlp_loss_and_grads(params, train)
        if epoch in {700, 1200}:
            lr *= 0.55
        for key in params:
            params[key] -= lr * grads[key]
        if epoch == 1 or epoch % 100 == 0 or epoch == epochs:
            train_probs = softmax(mlp_forward(params, train.x)[1])
            val_probs = softmax(mlp_forward(params, val.x)[1])
            history.append({
                "epoch": epoch,
                "train_loss": cross_entropy(train_probs, train.y),
                "train_acc": accuracy(train_probs, train.y),
                "val_acc": accuracy(val_probs, val.y),
            })
    return params, history


def eval_model(kind: str, params: dict[str, np.ndarray], split: Split) -> dict[str, float]:
    if kind == "linear":
        probs = softmax(linear_logits(params, split.x))
    elif kind == "mlp":
        probs = softmax(mlp_forward(params, split.x)[1])
    else:
        raise ValueError(kind)
    pred = probs.argmax(axis=1)
    tp = int(((pred == 1) & (split.y == 1)).sum())
    tn = int(((pred == 0) & (split.y == 0)).sum())
    fp = int(((pred == 1) & (split.y == 0)).sum())
    fn = int(((pred == 0) & (split.y == 1)).sum())
    return {
        "loss": cross_entropy(probs, split.y),
        "accuracy": accuracy(probs, split.y),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def gradient_check() -> dict[str, float]:
    rng = np.random.default_rng(21)
    params = init_mlp(rng, hidden=5)
    x = rng.normal(size=(8, 2))
    y = rng.integers(0, 2, size=8)
    split = Split(x, y)
    base_loss, grads = mlp_loss_and_grads(params, split)
    checks: list[float] = []
    eps = 1e-5
    for name, index in [("W1", (0, 0)), ("b1", (1,)), ("W2", (2, 1)), ("b2", (0,))]:
        original = float(params[name][index])
        params[name][index] = original + eps
        loss_plus, _ = mlp_loss_and_grads(params, split)
        params[name][index] = original - eps
        loss_minus, _ = mlp_loss_and_grads(params, split)
        params[name][index] = original
        numeric = (loss_plus - loss_minus) / (2 * eps)
        analytic = float(grads[name][index])
        rel_error = abs(numeric - analytic) / max(1.0, abs(numeric), abs(analytic))
        checks.append(rel_error)
    return {"base_loss": base_loss, "max_relative_error": float(max(checks)), "checked_values": len(checks)}


def save_dataset_csv(path: Path, split_name: str, split: Split) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["split", "x0", "x1", "label"])
        for row, label in zip(split.x, split.y):
            writer.writerow([split_name, f"{row[0]:.8f}", f"{row[1]:.8f}", int(label)])


def write_history_csv(path: Path, history: Iterable[dict[str, float]]) -> None:
    rows = list(history)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "train_loss", "train_acc", "val_acc"])
        writer.writeheader()
        writer.writerows(rows)


def write_svg(path: Path, linear_history: list[dict[str, float]], mlp_history: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 820, 440
    left, top, chart_w, chart_h = 80, 60, 660, 280
    max_epoch = max(int(row["epoch"]) for row in mlp_history)
    def point(row: dict[str, float], key: str) -> tuple[float, float]:
        x = left + int(row["epoch"]) / max_epoch * chart_w
        y = top + (1.0 - float(row[key])) * chart_h
        return x, y
    def polyline(rows: list[dict[str, float]], key: str) -> str:
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(row, key) for row in rows))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Validation accuracy by training epoch</title>',
        '<desc id="desc">Linear baseline and NumPy MLP validation accuracy during training.</desc>',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif}.title{font-size:22px;font-weight:700;fill:#0f172a}.axis{stroke:#475569;stroke-width:1.5}.grid{stroke:#e2e8f0}.label{font-size:13px;fill:#334155}.legend{font-size:14px;font-weight:700}.linear{fill:none;stroke:#64748b;stroke-width:3}.mlp{fill:none;stroke:#dc2626;stroke-width:3}</style>',
        '<text class="title" x="80" y="34">Validation accuracy by training epoch</text>',
    ]
    for tick in range(6):
        value = tick / 5
        y = top + (1 - value) * chart_h
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left+chart_w}" y2="{y:.1f}"/>')
        parts.append(f'<text class="label" x="{left-10}" y="{y+4:.1f}" text-anchor="end">{value:.1f}</text>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+chart_h}"/>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top+chart_h}" x2="{left+chart_w}" y2="{top+chart_h}"/>')
    parts.append(f'<polyline class="linear" points="{polyline(linear_history, "val_acc")}"/>')
    parts.append(f'<polyline class="mlp" points="{polyline(mlp_history, "val_acc")}"/>')
    parts.append('<text class="legend" x="560" y="86" fill="#64748b">linear baseline</text>')
    parts.append('<text class="legend" x="560" y="110" fill="#dc2626">MLP</text>')
    parts.append(f'<text class="label" x="{left+chart_w/2}" y="{height-24}" text-anchor="middle">Epoch; source: reports/*-history.csv</text>')
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def write_markdown(path: Path, metrics: dict[str, object]) -> None:
    lines = [
        "# Deep learning AI engineering report",
        "",
        "## Headline",
        "",
        f"- Seed: {metrics['seed']}",
        f"- Train/val/test rows: {metrics['rows']['train']}/{metrics['rows']['val']}/{metrics['rows']['test']}",
        f"- Majority test accuracy: {metrics['majority']['test']['accuracy']:.3f}",
        f"- Linear test accuracy: {metrics['linear']['test']['accuracy']:.3f}",
        f"- MLP test accuracy: {metrics['mlp']['test']['accuracy']:.3f}",
        f"- MLP minus linear accuracy: {metrics['comparison']['mlp_minus_linear_test_acc']:.3f}",
        f"- Gradient max relative error: {metrics['gradient_check']['max_relative_error']:.2e}",
        f"- Inference demo label: {metrics['inference_demo']['predicted_label']}",
        "",
        "## Artifacts",
        "",
        "- `reports/metrics.json`",
        "- `reports/training_curve.svg`",
        "- `reports/linear-history.csv`",
        "- `reports/mlp-history.csv`",
        "- `models/mlp-weights.npz`",
        "- `models/model-card.md`",
        "- `reports/transcript.txt`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_model_card(path: Path, metrics: dict[str, object]) -> None:
    lines = [
        "# Model card: NumPy MLP spiral classifier",
        "",
        "## Intended use",
        "Teaching-only two-class toy classification. It is not a real-world decision model.",
        "",
        "## Training data",
        "Synthetic two-dimensional spiral data generated with a fixed random seed.",
        "",
        "## Baselines",
        f"- Majority test accuracy: {metrics['majority']['test']['accuracy']:.3f}",
        f"- Linear softmax test accuracy: {metrics['linear']['test']['accuracy']:.3f}",
        f"- MLP test accuracy: {metrics['mlp']['test']['accuracy']:.3f}",
        "",
        "## Limitations",
        "This lab demonstrates engineering workflow, reproducibility, and baseline comparison. It does not claim performance on external datasets.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def predict_one(params: dict[str, np.ndarray], raw_point: np.ndarray, normalization: dict[str, list[float]]) -> dict[str, object]:
    mean = np.array(normalization["mean"])
    std = np.array(normalization["std"])
    x = ((raw_point.reshape(1, 2) - mean) / std).astype(np.float64)
    probs = softmax(mlp_forward(params, x)[1])[0]
    return {"point": raw_point.tolist(), "probabilities": probs.tolist(), "predicted_label": int(probs.argmax())}


def run(root: Path, seed: int = 7) -> dict[str, object]:
    data_dir = root / "data"
    reports = root / "reports"
    models = root / "models"
    x, y = make_spiral(seed=seed)
    splits = split_and_standardize(x, y)
    train = splits["train"]  # type: ignore[assignment]
    val = splits["val"]  # type: ignore[assignment]
    test = splits["test"]  # type: ignore[assignment]
    normalization = splits["normalization"]  # type: ignore[assignment]
    assert isinstance(train, Split) and isinstance(val, Split) and isinstance(test, Split)
    save_dataset_csv(data_dir / "train.csv", "train", train)
    save_dataset_csv(data_dir / "val.csv", "val", val)
    save_dataset_csv(data_dir / "test.csv", "test", test)

    majority_label = train_majority(train)
    linear_params, linear_history = train_linear(train, val)
    mlp_params, mlp_history = train_mlp(train, val)
    grad = gradient_check()
    inference = predict_one(mlp_params, np.array([0.35, -0.15]), normalization)  # type: ignore[arg-type]

    metrics = {
        "seed": seed,
        "rows": {"train": len(train.y), "val": len(val.y), "test": len(test.y)},
        "normalization": normalization,
        "majority": {"label": majority_label, "test": eval_majority(majority_label, test)},
        "linear": {"train": eval_model("linear", linear_params, train), "val": eval_model("linear", linear_params, val), "test": eval_model("linear", linear_params, test)},
        "mlp": {"train": eval_model("mlp", mlp_params, train), "val": eval_model("mlp", mlp_params, val), "test": eval_model("mlp", mlp_params, test)},
        "comparison": {},
        "gradient_check": grad,
        "inference_demo": inference,
    }
    metrics["comparison"] = {
        "mlp_minus_majority_test_acc": metrics["mlp"]["test"]["accuracy"] - metrics["majority"]["test"]["accuracy"],  # type: ignore[index]
        "mlp_minus_linear_test_acc": metrics["mlp"]["test"]["accuracy"] - metrics["linear"]["test"]["accuracy"],  # type: ignore[index]
    }
    reports.mkdir(parents=True, exist_ok=True)
    models.mkdir(parents=True, exist_ok=True)
    (reports / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_history_csv(reports / "linear-history.csv", linear_history)
    write_history_csv(reports / "mlp-history.csv", mlp_history)
    write_svg(reports / "training_curve.svg", linear_history, mlp_history)
    np.savez(models / "mlp-weights.npz", **mlp_params, mean=np.array(normalization["mean"]), std=np.array(normalization["std"]))  # type: ignore[index]
    write_model_card(models / "model-card.md", metrics)
    write_markdown(reports / "report.md", metrics)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a tiny NumPy MLP with baseline comparison.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    metrics = run(args.root)
    print(f"rows_train={metrics['rows']['train']}")
    print(f"rows_val={metrics['rows']['val']}")
    print(f"rows_test={metrics['rows']['test']}")
    print(f"majority_test_acc={metrics['majority']['test']['accuracy']:.3f}")
    print(f"linear_test_acc={metrics['linear']['test']['accuracy']:.3f}")
    print(f"mlp_test_acc={metrics['mlp']['test']['accuracy']:.3f}")
    print(f"mlp_minus_linear_test_acc={metrics['comparison']['mlp_minus_linear_test_acc']:.3f}")
    print(f"gradient_max_relative_error={metrics['gradient_check']['max_relative_error']:.2e}")
    print(f"inference_predicted_label={metrics['inference_demo']['predicted_label']}")
    print("deep_learning_ai_status=ok")


if __name__ == "__main__":
    main()
