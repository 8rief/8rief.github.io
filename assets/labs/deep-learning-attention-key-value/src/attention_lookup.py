#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import permutations
from typing import Callable, Iterable

Key = str
Value = str
Vector = tuple[float, ...]

KEYS: tuple[Key, ...] = ("red", "blue", "green", "gold")
VALUES: tuple[Value, ...] = ("apple", "sky", "leaf", "coin")
KEY_SCALE = 2.0


@dataclass(frozen=True)
class MemorySlot:
    key: Key
    value: Value


@dataclass(frozen=True)
class Sample:
    name: str
    slots: tuple[MemorySlot, ...]
    query: Key
    label: Value


def one_hot(index: int, size: int, *, scale: float = 1.0) -> Vector:
    if not 0 <= index < size:
        raise ValueError("index out of range")
    return tuple(scale if i == index else 0.0 for i in range(size))


def key_vector(key: Key) -> Vector:
    if key not in KEYS:
        raise ValueError(f"unknown key {key}")
    return one_hot(KEYS.index(key), len(KEYS), scale=KEY_SCALE)


def value_vector(value: Value) -> Vector:
    if value not in VALUES:
        raise ValueError(f"unknown value {value}")
    return one_hot(VALUES.index(value), len(VALUES))


def vector_argmax(vector: Vector) -> int:
    return max(range(len(vector)), key=lambda index: (vector[index], -index))


def value_from_vector(vector: Vector) -> Value:
    return VALUES[vector_argmax(vector)]


def dot(left: Vector, right: Vector) -> float:
    if len(left) != len(right):
        raise ValueError("dot product needs equal vector sizes")
    return sum(a * b for a, b in zip(left, right))


def softmax(scores: Iterable[float]) -> list[float]:
    rows = list(scores)
    if not rows:
        raise ValueError("softmax needs at least one score")
    max_score = max(rows)
    exps = [math.exp(score - max_score) for score in rows]
    total = sum(exps)
    return [value / total for value in exps]


def weighted_sum(weights: list[float], vectors: list[Vector]) -> Vector:
    if len(weights) != len(vectors):
        raise ValueError("weights and vectors length mismatch")
    if not vectors:
        raise ValueError("weighted sum needs vectors")
    width = len(vectors[0])
    if any(len(vector) != width for vector in vectors):
        raise ValueError("all vectors must have same width")
    return tuple(sum(weight * vector[i] for weight, vector in zip(weights, vectors)) for i in range(width))


def scaled_dot_product_attention(query: Vector, keys: list[Vector], values: list[Vector]) -> tuple[Vector, list[float], list[float]]:
    if not keys or not values:
        raise ValueError("attention needs at least one key/value slot")
    if len(keys) != len(values):
        raise ValueError("key/value slot count mismatch")
    scale = 1.0 / math.sqrt(len(query))
    scores = [dot(query, key) * scale for key in keys]
    weights = softmax(scores)
    output = weighted_sum(weights, values)
    return output, weights, scores


def make_assignment(values: tuple[Value, ...]) -> tuple[MemorySlot, ...]:
    if sorted(values) != sorted(VALUES):
        raise ValueError("assignment must contain each value exactly once")
    return tuple(MemorySlot(key, value) for key, value in zip(KEYS, values))


def make_sample(split: str, assignment_index: int, slots: tuple[MemorySlot, ...], query: Key) -> Sample:
    label_by_key = {slot.key: slot.value for slot in slots}
    return Sample(
        name=f"{split}-{assignment_index}-{query}",
        slots=slots,
        query=query,
        label=label_by_key[query],
    )


def make_dataset() -> tuple[list[Sample], list[Sample]]:
    all_assignments = [make_assignment(tuple(values)) for values in permutations(VALUES)]
    train_assignments = all_assignments[::3]
    test_assignments = all_assignments[1::3]
    train: list[Sample] = []
    test: list[Sample] = []
    for index, slots in enumerate(train_assignments):
        for query in KEYS:
            train.append(make_sample("train", index, slots, query))
    for index, slots in enumerate(test_assignments):
        for query in KEYS:
            test.append(make_sample("test", index, slots, query))
    return train, test


def majority_label(samples: Iterable[Sample]) -> Value:
    counts = Counter(sample.label for sample in samples)
    if not counts:
        raise ValueError("majority baseline needs samples")
    return sorted((-count, value) for value, count in counts.items())[0][1]


def bag_key(slots: tuple[MemorySlot, ...]) -> tuple[Value, ...]:
    return tuple(sorted(slot.value for slot in slots))


def train_lookup(
    samples: Iterable[Sample],
    key_fn: Callable[[Sample], object],
    *,
    default_label: Value,
) -> dict[object, Value]:
    buckets: dict[object, Counter[Value]] = defaultdict(Counter)
    for sample in samples:
        buckets[key_fn(sample)][sample.label] += 1
    table: dict[object, Value] = {}
    for key, counts in buckets.items():
        table[key] = sorted((-count, value) for value, count in counts.items())[0][1]
    table["__default__"] = default_label
    return table


def predict_from_lookup(sample: Sample, table: dict[object, Value], key_fn: Callable[[Sample], object]) -> Value:
    return table.get(key_fn(sample), table["__default__"])


def predict_last_value(sample: Sample) -> Value:
    return sample.slots[-1].value


def predict_fixed_summary(sample: Sample) -> Value:
    summary = weighted_sum(
        [1.0 / len(sample.slots)] * len(sample.slots),
        [value_vector(slot.value) for slot in sample.slots],
    )
    return value_from_vector(summary)


def attention_trace(sample: Sample) -> dict[str, object]:
    query = key_vector(sample.query)
    keys = [key_vector(slot.key) for slot in sample.slots]
    values = [value_vector(slot.value) for slot in sample.slots]
    output, weights, scores = scaled_dot_product_attention(query, keys, values)
    prediction = value_from_vector(output)
    top_index = vector_argmax(tuple(weights))
    return {
        "query": sample.query,
        "label": sample.label,
        "prediction": prediction,
        "slot_keys": [slot.key for slot in sample.slots],
        "slot_values": [slot.value for slot in sample.slots],
        "scores": [round(score, 6) for score in scores],
        "weights": [round(weight, 6) for weight in weights],
        "top_key": sample.slots[top_index].key,
        "top_value": sample.slots[top_index].value,
        "top_weight": weights[top_index],
        "output": [round(value, 6) for value in output],
    }


def predict_attention(sample: Sample) -> Value:
    return str(attention_trace(sample)["prediction"])


def accuracy(samples: Iterable[Sample], predict: Callable[[Sample], Value]) -> float:
    rows = list(samples)
    if not rows:
        raise ValueError("accuracy needs at least one sample")
    return sum(1 for sample in rows if predict(sample) == sample.label) / len(rows)


def trace_rows(samples: Iterable[Sample], bag_table: dict[object, Value]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sample in samples:
        trace = attention_trace(sample)
        rows.append({
            "name": sample.name,
            "query": sample.query,
            "label": sample.label,
            "slots": " ".join(f"{slot.key}:{slot.value}" for slot in sample.slots),
            "majority_prediction": VALUES[0],
            "last_value_prediction": predict_last_value(sample),
            "bag_prediction": predict_from_lookup(sample, bag_table, lambda item: bag_key(item.slots)),
            "fixed_summary_prediction": predict_fixed_summary(sample),
            "attention_prediction": trace["prediction"],
            "top_key": trace["top_key"],
            "top_weight": round(float(trace["top_weight"]), 6),
            "weights": " ".join(f"{slot.key}:{weight:.3f}" for slot, weight in zip(sample.slots, trace["weights"])),
        })
    return rows


def build_probe() -> dict[str, object]:
    train, test = make_dataset()
    majority = majority_label(train)
    bag_table = train_lookup(train, lambda sample: bag_key(sample.slots), default_label=majority)
    majority_acc = accuracy(test, lambda _sample: majority)
    last_value_acc = accuracy(test, predict_last_value)
    bag_acc = accuracy(test, lambda sample: predict_from_lookup(sample, bag_table, lambda item: bag_key(item.slots)))
    fixed_summary_acc = accuracy(test, predict_fixed_summary)
    attention_acc = accuracy(test, predict_attention)
    traces = [attention_trace(sample) for sample in test]
    min_top_weight = min(float(trace["top_weight"]) for trace in traces)
    all_top_keys_match = all(trace["top_key"] == trace["query"] for trace in traces)
    best_baseline = max(majority_acc, last_value_acc, bag_acc, fixed_summary_acc)
    run_ok = (
        majority_acc == 0.25
        and last_value_acc == 0.25
        and bag_acc == 0.25
        and fixed_summary_acc == 0.25
        and attention_acc == 1.0
        and min_top_weight > 0.70
        and all_top_keys_match
    )
    return {
        "schema_version": 1,
        "train_samples": len(train),
        "test_samples": len(test),
        "memory_slots": len(KEYS),
        "key_dim": len(KEYS),
        "value_dim": len(VALUES),
        "majority_baseline_accuracy": majority_acc,
        "last_value_accuracy": last_value_acc,
        "bag_of_values_accuracy": bag_acc,
        "fixed_summary_accuracy": fixed_summary_acc,
        "attention_lookup_accuracy": attention_acc,
        "attention_gain_over_best_baseline": attention_acc - best_baseline,
        "attention_min_top_weight": min_top_weight,
        "all_top_keys_match_query": all_top_keys_match,
        "trace_rows": trace_rows(test, bag_table),
        "boundary": "Pure-Python scaled dot-product attention over hand-built key/value vectors. This proves query-key-value lookup, not full Transformer training or language-model quality.",
        "run_status": "ok" if run_ok else "failed",
    }


def dumps_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    print(dumps_json(build_probe()))
