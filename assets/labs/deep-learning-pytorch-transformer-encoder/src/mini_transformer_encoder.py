#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

PAD = 0
CLS = 1
A = 2
B = 3
NOISE = 4
VOCAB = {"<pad>": PAD, "<cls>": CLS, "A": A, "B": B, "N": NOISE}
ID_TO_TOKEN = {value: key for key, value in VOCAB.items()}
LABELS = ["AA", "AB", "BA", "BB"]
LABEL_TO_ID = {label: index for index, label in enumerate(LABELS)}
MAX_LEN = 5


@dataclass(frozen=True)
class Sample:
    name: str
    tokens: tuple[int, int, int, int, int]
    label: int

    @property
    def label_name(self) -> str:
        return LABELS[self.label]

    @property
    def pair(self) -> tuple[int, int]:
        return (self.tokens[1], self.tokens[2])


def set_reproducible(seed: int = 20260713) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def pair_label(first: int, second: int) -> int:
    if first not in {A, B} or second not in {A, B}:
        raise ValueError("pair label expects A/B tokens")
    return LABEL_TO_ID[("A" if first == A else "B") + ("A" if second == A else "B")]


def make_samples(repeats: int, *, split: str) -> list[Sample]:
    base = [(A, A), (A, B), (B, A), (B, B)]
    rows: list[Sample] = []
    for rep in range(repeats):
        ordered = base if rep % 2 == 0 else list(reversed(base))
        for first, second in ordered:
            # Every row has the same length and one padding slot. The NOISE token is deliberately irrelevant.
            tokens = (CLS, first, second, NOISE, PAD)
            label = pair_label(first, second)
            rows.append(Sample(f"{split}-{rep}-{ID_TO_TOKEN[first]}{ID_TO_TOKEN[second]}", tokens, label))
    return rows


def make_train_test() -> tuple[list[Sample], list[Sample]]:
    return make_samples(12, split="train"), make_samples(2, split="test")


def accuracy(samples: Iterable[Sample], predict: Callable[[Sample], int]) -> float:
    rows = list(samples)
    if not rows:
        raise ValueError("accuracy needs samples")
    return sum(1 for sample in rows if predict(sample) == sample.label) / len(rows)


def majority_predictor(train: Iterable[Sample]) -> Callable[[Sample], int]:
    counts: dict[int, int] = {}
    for sample in train:
        counts[sample.label] = counts.get(sample.label, 0) + 1
    majority = sorted((-count, label) for label, count in counts.items())[0][1]
    return lambda _sample: majority


def predict_last_token(sample: Sample) -> int:
    # Reads the second pair token and guesses A as the first token.
    second = sample.tokens[2]
    return pair_label(A, second)


def predict_bag_sorted(sample: Sample) -> int:
    # Sees the multiset of the two content tokens, not their order. AB and BA collide.
    first, second = sorted(sample.pair)
    return pair_label(first, second)


def samples_to_tensors(samples: list[Sample]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    input_ids = torch.tensor([sample.tokens for sample in samples], dtype=torch.long)
    labels = torch.tensor([sample.label for sample in samples], dtype=torch.long)
    padding_mask = input_ids.eq(PAD)
    return input_ids, labels, padding_mask


class TinyTransformerEncoderClassifier(nn.Module):
    def __init__(self, vocab_size: int = len(VOCAB), num_labels: int = len(LABELS), max_len: int = MAX_LEN, d_model: int = 16) -> None:
        super().__init__()
        self.max_len = max_len
        self.token_embedding = nn.Embedding(vocab_size, d_model, padding_idx=PAD)
        self.position_embedding = nn.Embedding(max_len, d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=2,
            dim_feedforward=32,
            dropout=0.0,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=1, enable_nested_tensor=False)
        self.classifier = nn.Linear(d_model, num_labels)

    def forward(self, input_ids: torch.Tensor, padding_mask: torch.Tensor) -> torch.Tensor:
        if input_ids.ndim != 2:
            raise ValueError("input_ids must have shape (batch, seq)")
        batch, seq_len = input_ids.shape
        if seq_len > self.max_len:
            raise ValueError("sequence longer than max_len")
        positions = torch.arange(seq_len, device=input_ids.device).unsqueeze(0).expand(batch, seq_len)
        hidden = self.token_embedding(input_ids) + self.position_embedding(positions)
        encoded = self.encoder(hidden, src_key_padding_mask=padding_mask)
        cls_state = encoded[:, 0, :]
        return self.classifier(cls_state)


def evaluate(model: nn.Module, samples: list[Sample], device: torch.device) -> tuple[float, list[dict[str, object]]]:
    input_ids, labels, padding_mask = samples_to_tensors(samples)
    input_ids = input_ids.to(device)
    labels = labels.to(device)
    padding_mask = padding_mask.to(device)
    model.eval()
    rows: list[dict[str, object]] = []
    correct = 0
    with torch.no_grad():
        logits = model(input_ids, padding_mask)
        preds = logits.argmax(dim=1)
        correct = int(preds.eq(labels).sum().item())
        for sample, pred, logit in zip(samples, preds.cpu().tolist(), logits.cpu().tolist()):
            rows.append({
                "name": sample.name,
                "tokens": " ".join(ID_TO_TOKEN[token] for token in sample.tokens),
                "label": sample.label_name,
                "prediction": LABELS[pred],
                "correct": pred == sample.label,
                "logits": [round(float(value), 4) for value in logit],
            })
    return correct / len(samples), rows


def train_model(train: list[Sample], test: list[Sample], *, device_name: str = "cpu", epochs: int = 80) -> dict[str, object]:
    set_reproducible()
    device = torch.device(device_name)
    model = TinyTransformerEncoderClassifier().to(device)
    input_ids, labels, padding_mask = samples_to_tensors(train)
    dataset = TensorDataset(input_ids, labels, padding_mask)
    generator = torch.Generator().manual_seed(20260713)
    loader = DataLoader(dataset, batch_size=8, shuffle=True, generator=generator)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.03, weight_decay=0.0)
    history: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        total = 0
        for batch_input, batch_label, batch_mask in loader:
            batch_input = batch_input.to(device)
            batch_label = batch_label.to(device)
            batch_mask = batch_mask.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch_input, batch_mask)
            loss = criterion(logits, batch_label)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * int(batch_input.size(0))
            total += int(batch_input.size(0))
        if epoch in {1, 5, 20, epochs}:
            train_acc, _ = evaluate(model, train, device)
            test_acc, _ = evaluate(model, test, device)
            history.append({
                "epoch": float(epoch),
                "loss": total_loss / total,
                "train_accuracy": train_acc,
                "test_accuracy": test_acc,
            })
    train_acc, _ = evaluate(model, train, device)
    test_acc, prediction_rows = evaluate(model, test, device)
    return {
        "model": model,
        "history": history,
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "prediction_rows": prediction_rows,
    }


def checkpoint_reload_matches(model: nn.Module, test: list[Sample], device: torch.device, path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state_dict": model.state_dict(), "labels": LABELS, "vocab": VOCAB}, path)
    reloaded = TinyTransformerEncoderClassifier().to(device)
    try:
        snapshot = torch.load(path, map_location=device, weights_only=False)
    except TypeError:
        snapshot = torch.load(path, map_location=device)
    reloaded.load_state_dict(snapshot["model_state_dict"])
    original_acc, original_rows = evaluate(model, test, device)
    reload_acc, reload_rows = evaluate(reloaded, test, device)
    return original_acc == reload_acc and [row["prediction"] for row in original_rows] == [row["prediction"] for row in reload_rows]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write empty csv")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_probe(root: Path, *, device_name: str = "cpu") -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    train, test = make_train_test()
    majority_acc = accuracy(test, majority_predictor(train))
    last_acc = accuracy(test, predict_last_token)
    bag_acc = accuracy(test, predict_bag_sorted)
    training = train_model(train, test, device_name=device_name, epochs=80)
    model = training["model"]
    device = torch.device(device_name)
    checkpoint_ok = checkpoint_reload_matches(model, test, device, root / "checkpoint.pt")
    _input_ids, _labels, padding_mask = samples_to_tensors(test)
    history = training["history"]
    probe = {
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "device": device_name,
        "train_samples": len(train),
        "test_samples": len(test),
        "sequence_length": MAX_LEN,
        "label_count": len(LABELS),
        "majority_baseline_accuracy": majority_acc,
        "last_token_baseline_accuracy": last_acc,
        "bag_sorted_baseline_accuracy": bag_acc,
        "transformer_train_accuracy": training["train_accuracy"],
        "transformer_test_accuracy": training["test_accuracy"],
        "transformer_gain_over_best_baseline": training["test_accuracy"] - max(majority_acc, last_acc, bag_acc),
        "loss_decreased": history[-1]["loss"] < history[0]["loss"],
        "initial_loss": history[0]["loss"],
        "final_loss": history[-1]["loss"],
        "padding_mask_shape": list(padding_mask.shape),
        "padding_mask_true_count": int(padding_mask.sum().item()),
        "padding_mask_shape_ok": list(padding_mask.shape) == [len(test), MAX_LEN],
        "position_embedding_present": hasattr(model, "position_embedding"),
        "checkpoint_reload_match": checkpoint_ok,
        "run_status": "ok",
    }
    (root / "pytorch_transformer_probe.json").write_text(json.dumps(probe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(root / "training_history.csv", [{k: round(float(v), 6) for k, v in row.items()} for row in history])
    write_csv(root / "prediction_table.csv", training["prediction_rows"])
    report = [
        "# PyTorch mini Transformer encoder probe",
        "",
        f"- torch version: {probe['torch_version']}",
        f"- device: {probe['device']}",
        f"- train/test samples: {probe['train_samples']} / {probe['test_samples']}",
        f"- majority baseline accuracy: {probe['majority_baseline_accuracy']:.3f}",
        f"- last-token baseline accuracy: {probe['last_token_baseline_accuracy']:.3f}",
        f"- bag-sorted baseline accuracy: {probe['bag_sorted_baseline_accuracy']:.3f}",
        f"- transformer test accuracy: {probe['transformer_test_accuracy']:.3f}",
        f"- loss: {probe['initial_loss']:.4f} -> {probe['final_loss']:.4f}",
        f"- checkpoint reload match: {probe['checkpoint_reload_match']}",
        f"- run status: {probe['run_status']}",
        "",
    ]
    (root / "pytorch_transformer_report.md").write_text("\n".join(report), encoding="utf-8")
    return probe
