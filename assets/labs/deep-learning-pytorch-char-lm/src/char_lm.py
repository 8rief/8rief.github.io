"""Tiny PyTorch character language model used by the teaching blog lab.

The corpus is synthetic on purpose. It has a long-range cue: the first
character determines the final label after a shared delimiter, so a bigram
baseline cannot solve the final-token prediction from the previous character
alone. The lab teaches the pipeline and the boundary, not natural-language
quality.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import torch
from torch import nn
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset

PAD = "<pad>"
BOS = "<bos>"
EOS = "<eos>"
CUES = {"a": "A", "b": "B", "c": "C"}
CUE_ORDER = ["a", "b", "c"]
LABELS = ["A", "B", "C"]

# Shared middle strings use the same character alphabet across splits. Holding
# out a whole alphabet would test out-of-vocabulary handling rather than the
# language-model objective we want here.
TRAIN_MIDDLES = ["mno", "nrm", "orn", "rom", "mon", "nom"]
VAL_MIDDLES = ["mro", "onm", "rno"]
TEST_MIDDLES = ["nmo", "orm", "rnm"]


@dataclass(frozen=True)
class CharExample:
    raw: str
    cue: str

    @property
    def label(self) -> str:
        return CUES[self.cue]

    @property
    def label_index(self) -> int:
        return len(self.raw) - 1


@dataclass(frozen=True)
class Batch:
    input_ids: torch.Tensor
    target_ids: torch.Tensor
    lengths: torch.Tensor
    label_positions: torch.Tensor
    raw: list[str]
    cues: list[str]


def build_examples(middles: Sequence[str]) -> list[CharExample]:
    examples: list[CharExample] = []
    for middle in middles:
        for cue in CUE_ORDER:
            examples.append(CharExample(raw=f"{cue}{middle}|{CUES[cue]}", cue=cue))
    return examples


def split_examples() -> dict[str, list[CharExample]]:
    return {
        "train": build_examples(TRAIN_MIDDLES),
        "val": build_examples(VAL_MIDDLES),
        "test": build_examples(TEST_MIDDLES),
    }


def build_vocab(examples: Iterable[CharExample]) -> dict[str, int]:
    chars = sorted({char for example in examples for char in example.raw})
    vocab = {PAD: 0, BOS: 1, EOS: 2}
    for char in chars:
        if char not in vocab:
            vocab[char] = len(vocab)
    return vocab


def inverse_vocab(vocab: dict[str, int]) -> dict[int, str]:
    return {idx: token for token, idx in vocab.items()}


def encode_example(example: CharExample, vocab: dict[str, int]) -> tuple[torch.Tensor, torch.Tensor, int]:
    # Teacher forcing: at training time the input at step t is the gold previous
    # character, while the target at step t is the next gold character.
    input_tokens = [BOS, *example.raw]
    target_tokens = [*example.raw, EOS]
    input_ids = torch.tensor([vocab[token] for token in input_tokens], dtype=torch.long)
    target_ids = torch.tensor([vocab[token] for token in target_tokens], dtype=torch.long)
    return input_ids, target_ids, example.label_index


class CharDataset(Dataset[CharExample]):
    def __init__(self, examples: Sequence[CharExample]) -> None:
        self.examples = list(examples)

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> CharExample:
        return self.examples[index]


def make_collate_fn(vocab: dict[str, int]):
    pad_id = vocab[PAD]
    ignore_index = -100

    def collate(examples: list[CharExample]) -> Batch:
        encoded = [encode_example(example, vocab) for example in examples]
        inputs = [item[0] for item in encoded]
        targets = [item[1] for item in encoded]
        label_positions = torch.tensor([item[2] for item in encoded], dtype=torch.long)
        lengths = torch.tensor([len(item) for item in inputs], dtype=torch.long)
        input_ids = pad_sequence(inputs, batch_first=True, padding_value=pad_id)
        target_ids = pad_sequence(targets, batch_first=True, padding_value=ignore_index)
        return Batch(
            input_ids=input_ids,
            target_ids=target_ids,
            lengths=lengths,
            label_positions=label_positions,
            raw=[example.raw for example in examples],
            cues=[example.cue for example in examples],
        )

    return collate


def make_loader(
    examples: Sequence[CharExample],
    vocab: dict[str, int],
    *,
    batch_size: int,
    shuffle: bool,
    seed: int,
) -> DataLoader[Batch]:
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        CharDataset(examples),
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=make_collate_fn(vocab),
        generator=generator,
        num_workers=0,
    )


class CharGRULanguageModel(nn.Module):
    def __init__(self, vocab_size: int, embedding_dim: int, hidden_size: int, pad_id: int) -> None:
        super().__init__()
        self.pad_id = pad_id
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_id)
        self.gru = nn.GRU(embedding_dim, hidden_size, batch_first=True)
        self.output = nn.Linear(hidden_size, vocab_size)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(input_ids)
        states, _ = self.gru(embedded)
        return self.output(states)


def set_reproducibility(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def _sequence_pairs(examples: Sequence[CharExample]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for example in examples:
        previous = BOS
        for char in [*example.raw, EOS]:
            pairs.append((previous, char))
            previous = char
    return pairs


def unigram_baseline(train: Sequence[CharExample], test: Sequence[CharExample]) -> dict[str, float | str]:
    target_counts = Counter(target for _, target in _sequence_pairs(train))
    prediction = min((-count, token) for token, count in target_counts.items())[1]
    correct = 0
    total = 0
    final_correct = 0
    for example in test:
        targets = [*example.raw, EOS]
        for pos, target in enumerate(targets):
            correct += int(prediction == target)
            if pos == example.label_index:
                final_correct += int(prediction == target)
            total += 1
    return {"token_accuracy": correct / total, "final_accuracy": final_correct / len(test), "prediction": prediction}


def bigram_baseline(train: Sequence[CharExample], test: Sequence[CharExample]) -> dict[str, float | str]:
    next_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for previous, target in _sequence_pairs(train):
        next_counts[previous][target] += 1
    global_counts = Counter(target for _, target in _sequence_pairs(train))
    global_prediction = min((-count, token) for token, count in global_counts.items())[1]

    def predict(previous: str) -> str:
        counts = next_counts.get(previous)
        if not counts:
            return global_prediction
        return min((-count, token) for token, count in counts.items())[1]

    correct = 0
    total = 0
    final_correct = 0
    final_predictions: list[str] = []
    for example in test:
        previous = BOS
        for pos, target in enumerate([*example.raw, EOS]):
            pred = predict(previous)
            correct += int(pred == target)
            if pos == example.label_index:
                final_correct += int(pred == target)
                final_predictions.append(pred)
            total += 1
            previous = target
    return {
        "token_accuracy": correct / total,
        "final_accuracy": final_correct / len(test),
        "delimiter_prediction": predict("|"),
        "final_predictions": "".join(final_predictions),
    }


def uniform_nll(vocab_size: int) -> float:
    return math.log(vocab_size)


def evaluate_model(model: CharGRULanguageModel, loader: DataLoader[Batch], loss_fn: nn.Module, vocab: dict[str, int]) -> dict[str, Any]:
    model.eval()
    id_to_token = inverse_vocab(vocab)
    total_loss = 0.0
    total_tokens = 0
    correct_tokens = 0
    final_correct = 0
    final_rows: list[dict[str, Any]] = []
    with torch.no_grad():
        for batch in loader:
            logits = model(batch.input_ids)
            loss = loss_fn(logits.reshape(-1, logits.size(-1)), batch.target_ids.reshape(-1))
            mask = batch.target_ids.ne(-100)
            preds = logits.argmax(dim=-1)
            token_count = int(mask.sum().item())
            total_loss += float(loss.item()) * token_count
            total_tokens += token_count
            correct_tokens += int(((preds == batch.target_ids) & mask).sum().item())
            for row_idx, pos in enumerate(batch.label_positions.tolist()):
                gold_id = int(batch.target_ids[row_idx, pos].item())
                pred_id = int(preds[row_idx, pos].item())
                final_correct += int(gold_id == pred_id)
                top_values, top_ids = torch.softmax(logits[row_idx, pos], dim=-1).topk(3)
                final_rows.append(
                    {
                        "raw": batch.raw[row_idx],
                        "cue": batch.cues[row_idx],
                        "gold": id_to_token[gold_id],
                        "pred": id_to_token[pred_id],
                        "top3": [(id_to_token[int(idx)], float(value)) for value, idx in zip(top_values, top_ids)],
                    }
                )
    return {
        "nll": total_loss / total_tokens,
        "token_accuracy": correct_tokens / total_tokens,
        "final_accuracy": final_correct / len(loader.dataset),
        "final_rows": final_rows,
    }


def train_model(
    train: Sequence[CharExample],
    val: Sequence[CharExample],
    vocab: dict[str, int],
    *,
    seed: int = 20260714,
    epochs: int = 160,
    batch_size: int = 9,
) -> tuple[CharGRULanguageModel, list[dict[str, float]]]:
    set_reproducibility(seed)
    model = CharGRULanguageModel(vocab_size=len(vocab), embedding_dim=12, hidden_size=24, pad_id=vocab[PAD])
    loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.035, weight_decay=0.0)
    train_loader = make_loader(train, vocab, batch_size=batch_size, shuffle=True, seed=seed)
    val_loader = make_loader(val, vocab, batch_size=batch_size, shuffle=False, seed=seed)
    history: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        for batch in train_loader:
            logits = model(batch.input_ids)
            loss = loss_fn(logits.reshape(-1, logits.size(-1)), batch.target_ids.reshape(-1))
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
        if epoch in {1, 2, 5, 10, 20, 40, 80, 120, epochs}:
            train_metrics = evaluate_model(model, train_loader, loss_fn, vocab)
            val_metrics = evaluate_model(model, val_loader, loss_fn, vocab)
            history.append(
                {
                    "epoch": float(epoch),
                    "train_nll": float(train_metrics["nll"]),
                    "train_final_acc": float(train_metrics["final_accuracy"]),
                    "val_nll": float(val_metrics["nll"]),
                    "val_final_acc": float(val_metrics["final_accuracy"]),
                }
            )
    return model, history


def predict_next_char(model: CharGRULanguageModel, vocab: dict[str, int], prefix: str) -> tuple[str, float, list[tuple[str, float]]]:
    model.eval()
    id_to_token = inverse_vocab(vocab)
    input_ids = torch.tensor([[vocab[BOS], *[vocab[ch] for ch in prefix]]], dtype=torch.long)
    with torch.no_grad():
        logits = model(input_ids)[0, -1]
        probs = torch.softmax(logits, dim=-1)
        top_values, top_ids = probs.topk(3)
    top3 = [(id_to_token[int(idx)], float(value)) for value, idx in zip(top_values, top_ids)]
    return top3[0][0], top3[0][1], top3


def greedy_generate(model: CharGRULanguageModel, vocab: dict[str, int], prefix: str, *, max_new_chars: int = 8) -> str:
    generated = prefix
    for _ in range(max_new_chars):
        next_char, _, _ = predict_next_char(model, vocab, generated)
        if next_char == EOS:
            break
        generated += next_char
    return generated


def save_history(path: Path, history: Sequence[dict[str, float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["epoch", "train_nll", "train_final_acc", "val_nll", "val_final_acc"])
        writer.writeheader()
        for row in history:
            writer.writerow(row)


def save_final_predictions(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["raw", "cue", "gold", "pred", "top3"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "top3": json.dumps(row["top3"], ensure_ascii=False)})
