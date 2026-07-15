#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable

Sequence = tuple[str, ...]
Label = str

LABEL_A = "topic_a"
LABEL_B = "topic_b"
RECURRENT_WEIGHT = 2.0
INPUT_WEIGHT = 3.0


@dataclass(frozen=True)
class Sample:
    name: str
    sequence: Sequence
    label: Label


def make_sample(split: str, label_token: str, suffix: str, index: int) -> Sample:
    if label_token not in {"A", "B"}:
        raise ValueError("label token must be A or B")
    if any(token not in {"x", "y"} for token in suffix):
        raise ValueError("suffix tokens must be x/y")
    label = LABEL_A if label_token == "A" else LABEL_B
    sequence = tuple(label_token + suffix)
    return Sample(f"{split}-{index}-{label_token}-{suffix}", sequence, label)


def make_dataset() -> tuple[list[Sample], list[Sample]]:
    train_suffixes = ["xxyxy", "xyxxy", "yxxxy", "xyyxx"]
    test_suffixes = ["yyxxx", "yxyxx", "xxyyx", "yxxyx"]
    train: list[Sample] = []
    test: list[Sample] = []
    for index, suffix in enumerate(train_suffixes):
        train.append(make_sample("train", "A", suffix, index))
        train.append(make_sample("train", "B", suffix, index))
    for index, suffix in enumerate(test_suffixes):
        test.append(make_sample("test", "A", suffix, index))
        test.append(make_sample("test", "B", suffix, index))
    return train, test


def token_input(token: str) -> float:
    if token == "A":
        return 1.0
    if token == "B":
        return -1.0
    if token in {"x", "y"}:
        return 0.0
    raise ValueError(f"unknown token {token}")


def recurrent_step(previous_hidden: float, token: str, *, recurrent_weight: float = RECURRENT_WEIGHT) -> float:
    return math.tanh(recurrent_weight * previous_hidden + INPUT_WEIGHT * token_input(token))


def trace_sequence(sequence: Sequence, *, recurrent_weight: float = RECURRENT_WEIGHT) -> list[float]:
    hidden = 0.0
    trace: list[float] = []
    for token in sequence:
        hidden = recurrent_step(hidden, token, recurrent_weight=recurrent_weight)
        trace.append(hidden)
    return trace


def predict_recurrent(sequence: Sequence) -> Label:
    final_hidden = trace_sequence(sequence)[-1]
    return LABEL_A if final_hidden >= 0.0 else LABEL_B


def predict_no_recurrence(sequence: Sequence) -> Label:
    final_hidden = trace_sequence(sequence, recurrent_weight=0.0)[-1]
    return LABEL_A if final_hidden >= 0.0 else LABEL_B


def majority_label(samples: Iterable[Sample]) -> Label:
    counts = Counter(sample.label for sample in samples)
    if not counts:
        raise ValueError("majority baseline needs samples")
    return sorted((-count, label) for label, count in counts.items())[0][1]


def suffix_bag_key(sequence: Sequence) -> tuple[tuple[str, int], ...]:
    counts = Counter(sequence[1:])
    return tuple(sorted(counts.items()))


def train_lookup(
    samples: Iterable[Sample],
    key_fn: Callable[[Sequence], object],
    *,
    default_label: Label,
) -> dict[object, Label]:
    buckets: dict[object, Counter[Label]] = defaultdict(Counter)
    for sample in samples:
        buckets[key_fn(sample.sequence)][sample.label] += 1
    table: dict[object, Label] = {}
    for key, counts in buckets.items():
        table[key] = sorted((-count, label) for label, count in counts.items())[0][1]
    table["__default__"] = default_label
    return table


def predict_from_lookup(sequence: Sequence, table: dict[object, Label], key_fn: Callable[[Sequence], object]) -> Label:
    return table.get(key_fn(sequence), table["__default__"])


def accuracy(samples: Iterable[Sample], predict: Callable[[Sequence], Label]) -> float:
    rows = list(samples)
    if not rows:
        raise ValueError("accuracy needs at least one sample")
    return sum(1 for sample in rows if predict(sample.sequence) == sample.label) / len(rows)


def hidden_sign_stable(samples: Iterable[Sample]) -> bool:
    for sample in samples:
        expected_positive = sample.label == LABEL_A
        trace = trace_sequence(sample.sequence)
        if expected_positive and any(value <= 0.0 for value in trace):
            return False
        if not expected_positive and any(value >= 0.0 for value in trace):
            return False
    return True


def trace_rows(samples: Iterable[Sample], suffix_table: dict[object, Label], last_table: dict[object, Label]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sample in samples:
        trace = trace_sequence(sample.sequence)
        rows.append({
            "name": sample.name,
            "sequence": "".join(sample.sequence),
            "label": sample.label,
            "last_token_prediction": predict_from_lookup(sample.sequence, last_table, lambda seq: seq[-1]),
            "suffix_bag_prediction": predict_from_lookup(sample.sequence, suffix_table, suffix_bag_key),
            "no_recurrence_prediction": predict_no_recurrence(sample.sequence),
            "rnn_prediction": predict_recurrent(sample.sequence),
            "hidden_after_first": round(trace[0], 4),
            "final_hidden": round(trace[-1], 4),
        })
    return rows


def build_probe() -> dict[str, object]:
    train, test = make_dataset()
    majority = majority_label(train)
    suffix_table = train_lookup(train, suffix_bag_key, default_label=majority)
    last_table = train_lookup(train, lambda seq: seq[-1], default_label=majority)
    majority_acc = accuracy(test, lambda _seq: majority)
    last_token_acc = accuracy(test, lambda seq: predict_from_lookup(seq, last_table, lambda item: item[-1]))
    suffix_bag_acc = accuracy(test, lambda seq: predict_from_lookup(seq, suffix_table, suffix_bag_key))
    no_recurrence_acc = accuracy(test, predict_no_recurrence)
    recurrent_acc = accuracy(test, predict_recurrent)
    rows = trace_rows(test, suffix_table, last_table)
    best_baseline = max(majority_acc, last_token_acc, suffix_bag_acc, no_recurrence_acc)
    stable = hidden_sign_stable(train + test)
    return {
        "schema_version": 1,
        "train_samples": len(train),
        "test_samples": len(test),
        "sequence_length": len(train[0].sequence),
        "neutral_suffix_tokens": ["x", "y"],
        "majority_baseline_accuracy": majority_acc,
        "last_token_accuracy": last_token_acc,
        "suffix_bag_accuracy": suffix_bag_acc,
        "no_recurrence_accuracy": no_recurrence_acc,
        "rnn_memory_accuracy": recurrent_acc,
        "memory_gain_over_best_baseline": recurrent_acc - best_baseline,
        "hidden_sign_stable": stable,
        "trace_rows": rows,
        "boundary": "Synthetic delayed-cue sequences show hidden-state carry. This is not a language-model benchmark and the recurrent weights are hand chosen for mechanism clarity.",
        "run_status": "ok" if recurrent_acc == 1.0 and best_baseline == 0.5 and stable else "failed",
    }


def dumps_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    print(dumps_json(build_probe()))
