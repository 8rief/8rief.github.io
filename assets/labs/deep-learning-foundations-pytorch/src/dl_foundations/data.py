from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import torch
from torch.utils.data import TensorDataset


@dataclass(frozen=True)
class DatasetBundle:
    train_x: torch.Tensor
    train_y: torch.Tensor
    val_x: torch.Tensor
    val_y: torch.Tensor
    test_x: torch.Tensor
    test_y: torch.Tensor

    def as_dataset(self, split: str) -> TensorDataset:
        x, y = self.split(split)
        return TensorDataset(x, y)

    def split(self, split: str) -> Tuple[torch.Tensor, torch.Tensor]:
        if split == "train":
            return self.train_x, self.train_y
        if split == "val":
            return self.val_x, self.val_y
        if split == "test":
            return self.test_x, self.test_y
        raise ValueError(f"unknown split: {split}")

    def summary(self) -> dict[str, object]:
        return {
            "features": 2,
            "train": int(self.train_y.numel()),
            "val": int(self.val_y.numel()),
            "test": int(self.test_y.numel()),
            "train_positive_rate": float(self.train_y.mean().item()),
            "val_positive_rate": float(self.val_y.mean().item()),
            "test_positive_rate": float(self.test_y.mean().item()),
        }


def make_xor_gaussians(
    n_per_quadrant: int = 120,
    noise: float = 0.32,
    seed: int = 20260625,
) -> DatasetBundle:
    """Generate a deterministic nonlinear XOR-style binary classification task.

    Class 0 occupies the lower-left and upper-right clusters; class 1 occupies
    the upper-left and lower-right clusters. A single linear boundary cannot fit
    this pattern, so the lab has a meaningful linear baseline before the MLP.
    """

    rng = np.random.default_rng(seed)
    centers = np.array(
        [[-1.0, -1.0], [-1.0, 1.0], [1.0, -1.0], [1.0, 1.0]], dtype=np.float32
    )
    labels = np.array([0.0, 1.0, 1.0, 0.0], dtype=np.float32)

    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    for center, label in zip(centers, labels):
        xs.append(center + rng.normal(0.0, noise, size=(n_per_quadrant, 2)).astype(np.float32))
        ys.append(np.full((n_per_quadrant,), label, dtype=np.float32))

    x = np.concatenate(xs, axis=0)
    y = np.concatenate(ys, axis=0)
    order = rng.permutation(x.shape[0])
    x = x[order]
    y = y[order]

    n = x.shape[0]
    train_end = int(n * 0.60)
    val_end = int(n * 0.80)
    train_x_np, val_x_np, test_x_np = x[:train_end], x[train_end:val_end], x[val_end:]
    train_y_np, val_y_np, test_y_np = y[:train_end], y[train_end:val_end], y[val_end:]

    mean = train_x_np.mean(axis=0, keepdims=True)
    std = train_x_np.std(axis=0, keepdims=True)
    std = np.maximum(std, 1e-6)

    def norm(a: np.ndarray) -> torch.Tensor:
        return torch.tensor((a - mean) / std, dtype=torch.float32)

    return DatasetBundle(
        train_x=norm(train_x_np),
        train_y=torch.tensor(train_y_np, dtype=torch.float32),
        val_x=norm(val_x_np),
        val_y=torch.tensor(val_y_np, dtype=torch.float32),
        test_x=norm(test_x_np),
        test_y=torch.tensor(test_y_np, dtype=torch.float32),
    )
