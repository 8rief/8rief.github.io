from __future__ import annotations

import torch
from torch import nn


class LinearClassifier(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(2, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x).squeeze(-1)


class MLPClassifier(nn.Module):
    def __init__(self, hidden_dim: int = 16) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def build_model(name: str) -> nn.Module:
    if name == "linear":
        return LinearClassifier()
    if name == "mlp":
        return MLPClassifier()
    raise ValueError(f"unknown model: {name}")
