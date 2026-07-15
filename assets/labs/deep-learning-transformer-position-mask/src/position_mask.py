#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable

Token = str
Label = str
Vector = tuple[float, ...]

TOKENS: tuple[Token, ...] = ("A", "B")
POSITION_SCALE = 2.0


@dataclass(frozen=True)
class OrderSample:
    name: str
    sequence: tuple[Token, Token]
    query_position: int
    label: Label


@dataclass(frozen=True)
class FutureSample:
    name: str
    sequence: tuple[Token, Token, Token]
    query_index: int
    future_index: int
    label: Label


def one_hot(index: int, size: int, *, scale: float = 1.0) -> Vector:
    if not 0 <= index < size:
        raise ValueError("index out of range")
    return tuple(scale if i == index else 0.0 for i in range(size))


def token_vector(token: Token) -> Vector:
    if token not in TOKENS:
        raise ValueError(f"unknown token {token}")
    return one_hot(TOKENS.index(token), len(TOKENS))


def position_vector(position: int, size: int) -> Vector:
    return one_hot(position, size, scale=POSITION_SCALE)


def vector_argmax(vector: Vector) -> int:
    return max(range(len(vector)), key=lambda i: (vector[i], -i))


def token_from_vector(vector: Vector) -> Token:
    return TOKENS[vector_argmax(vector)]


def dot(left: Vector, right: Vector) -> float:
    if len(left) != len(right):
        raise ValueError("dot product needs equal vector sizes")
    return sum(a * b for a, b in zip(left, right))


def softmax(scores: Iterable[float]) -> list[float]:
    rows = list(scores)
    if not rows:
        raise ValueError("softmax needs scores")
    max_score = max(rows)
    exps = [math.exp(score - max_score) for score in rows]
    total = sum(exps)
    return [value / total for value in exps]


def weighted_sum(weights: list[float], vectors: list[Vector]) -> Vector:
    if len(weights) != len(vectors):
        raise ValueError("weights and vectors length mismatch")
    width = len(vectors[0])
    if any(len(vector) != width for vector in vectors):
        raise ValueError("all vectors must have same width")
    return tuple(sum(weight * vector[i] for weight, vector in zip(weights, vectors)) for i in range(width))


def scaled_dot_product_attention(
    query: Vector,
    keys: list[Vector],
    values: list[Vector],
    *,
    allowed: list[bool] | None = None,
) -> tuple[Vector, list[float], list[float]]:
    if len(keys) != len(values):
        raise ValueError("key/value count mismatch")
    if allowed is not None and len(allowed) != len(keys):
        raise ValueError("mask length mismatch")
    scale = 1.0 / math.sqrt(len(query))
    raw_scores = [dot(query, key) * scale for key in keys]
    if allowed is None:
        masked_scores = raw_scores
    else:
        if not any(allowed):
            raise ValueError("attention mask must allow at least one slot")
        masked_scores = [score if keep else float("-inf") for score, keep in zip(raw_scores, allowed)]
    weights = softmax(masked_scores)
    output = weighted_sum(weights, values)
    return output, weights, raw_scores


def make_order_dataset() -> tuple[list[OrderSample], list[OrderSample]]:
    base = [
        OrderSample("order-ab", ("A", "B"), 0, "A"),
        OrderSample("order-ba", ("B", "A"), 0, "B"),
    ]
    train = [OrderSample(f"train-{i}-{sample.name}", sample.sequence, sample.query_position, sample.label) for i in range(4) for sample in base]
    test = [OrderSample(f"test-{i}-{sample.name}", sample.sequence, sample.query_position, sample.label) for i in range(4) for sample in reversed(base)]
    return train, test


def make_future_dataset() -> tuple[list[FutureSample], list[FutureSample]]:
    base = [
        FutureSample("future-a", ("A", "A", "A"), 1, 2, "A"),
        FutureSample("future-b", ("A", "A", "B"), 1, 2, "B"),
    ]
    train = [FutureSample(f"train-{i}-{sample.name}", sample.sequence, sample.query_index, sample.future_index, sample.label) for i in range(4) for sample in base]
    test = [FutureSample(f"test-{i}-{sample.name}", sample.sequence, sample.query_index, sample.future_index, sample.label) for i in range(4) for sample in reversed(base)]
    return train, test


def majority_label(labels: Iterable[Label]) -> Label:
    counts = Counter(labels)
    if not counts:
        raise ValueError("majority needs labels")
    return sorted((-count, label) for label, count in counts.items())[0][1]


def accuracy(samples: Iterable[object], predict: Callable[[object], Label]) -> float:
    rows = list(samples)
    if not rows:
        raise ValueError("accuracy needs samples")
    return sum(1 for sample in rows if predict(sample) == sample.label) / len(rows)  # type: ignore[attr-defined]


def predict_bag_order(sample: OrderSample) -> Label:
    counts = Counter(sample.sequence)
    # Both order samples contain A and B once, so this deterministic tie-break loses order.
    return sorted((-count, token) for token, count in counts.items())[0][1]


def no_position_attention_trace(sample: OrderSample) -> dict[str, object]:
    # Query asks for "position 0", but keys carry only token identity, so both slots look equally unrelated.
    query = (0.0, 0.0)
    keys = [token_vector(token) for token in sample.sequence]
    values = [token_vector(token) for token in sample.sequence]
    output, weights, scores = scaled_dot_product_attention(query, keys, values)
    return {
        "prediction": token_from_vector(output),
        "weights": weights,
        "scores": scores,
        "output": output,
    }


def predict_no_position_attention(sample: OrderSample) -> Label:
    return str(no_position_attention_trace(sample)["prediction"])


def positional_attention_trace(sample: OrderSample) -> dict[str, object]:
    query = position_vector(sample.query_position, len(sample.sequence))
    keys = [position_vector(index, len(sample.sequence)) for index, _token in enumerate(sample.sequence)]
    values = [token_vector(token) for token in sample.sequence]
    output, weights, scores = scaled_dot_product_attention(query, keys, values)
    top_index = vector_argmax(tuple(weights))
    return {
        "prediction": token_from_vector(output),
        "weights": weights,
        "scores": scores,
        "top_position": top_index,
        "top_weight": weights[top_index],
        "output": output,
    }


def predict_positional_attention(sample: OrderSample) -> Label:
    return str(positional_attention_trace(sample)["prediction"])


def future_lookup_trace(sample: FutureSample, *, causal: bool) -> dict[str, object]:
    query = position_vector(sample.future_index, len(sample.sequence))
    keys = [position_vector(index, len(sample.sequence)) for index, _token in enumerate(sample.sequence)]
    values = [token_vector(token) for token in sample.sequence]
    allowed = None
    if causal:
        allowed = [index <= sample.query_index for index, _token in enumerate(sample.sequence)]
    output, weights, scores = scaled_dot_product_attention(query, keys, values, allowed=allowed)
    future_weight = weights[sample.future_index]
    return {
        "prediction": token_from_vector(output),
        "weights": weights,
        "scores": scores,
        "future_weight": future_weight,
        "output": output,
        "causal": causal,
    }


def predict_unmasked_future_lookup(sample: FutureSample) -> Label:
    return str(future_lookup_trace(sample, causal=False)["prediction"])


def predict_causal_masked_lookup(sample: FutureSample) -> Label:
    return str(future_lookup_trace(sample, causal=True)["prediction"])


def order_trace_rows(samples: Iterable[OrderSample]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sample in samples:
        no_pos = no_position_attention_trace(sample)
        pos = positional_attention_trace(sample)
        rows.append({
            "name": sample.name,
            "sequence": "".join(sample.sequence),
            "label": sample.label,
            "bag_prediction": predict_bag_order(sample),
            "no_position_prediction": no_pos["prediction"],
            "positional_prediction": pos["prediction"],
            "positional_top_position": pos["top_position"],
            "positional_top_weight": round(float(pos["top_weight"]), 6),
            "no_position_weights": " ".join(f"{weight:.3f}" for weight in no_pos["weights"]),
            "positional_weights": " ".join(f"{weight:.3f}" for weight in pos["weights"]),
        })
    return rows


def future_trace_rows(samples: Iterable[FutureSample]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sample in samples:
        unmasked = future_lookup_trace(sample, causal=False)
        masked = future_lookup_trace(sample, causal=True)
        rows.append({
            "name": sample.name,
            "sequence": "".join(sample.sequence),
            "query_index": sample.query_index,
            "future_index": sample.future_index,
            "label": sample.label,
            "unmasked_prediction": unmasked["prediction"],
            "causal_masked_prediction": masked["prediction"],
            "unmasked_future_weight": round(float(unmasked["future_weight"]), 6),
            "masked_future_weight": round(float(masked["future_weight"]), 6),
            "unmasked_weights": " ".join(f"{weight:.3f}" for weight in unmasked["weights"]),
            "masked_weights": " ".join(f"{weight:.3f}" for weight in masked["weights"]),
        })
    return rows


def build_probe() -> dict[str, object]:
    _order_train, order_test = make_order_dataset()
    _future_train, future_test = make_future_dataset()
    position_bag_acc = accuracy(order_test, predict_bag_order)
    no_position_acc = accuracy(order_test, predict_no_position_attention)
    positional_acc = accuracy(order_test, predict_positional_attention)
    positional_traces = [positional_attention_trace(sample) for sample in order_test]
    min_position_top_weight = min(float(trace["top_weight"]) for trace in positional_traces)
    positional_top_matches = all(trace["top_position"] == sample.query_position for trace, sample in zip(positional_traces, order_test))
    unmasked_acc = accuracy(future_test, predict_unmasked_future_lookup)
    causal_acc = accuracy(future_test, predict_causal_masked_lookup)
    future_traces = [future_lookup_trace(sample, causal=True) for sample in future_test]
    mask_blocks_future = all(float(trace["future_weight"]) == 0.0 for trace in future_traces)
    run_ok = (
        position_bag_acc == 0.5
        and no_position_acc == 0.5
        and positional_acc == 1.0
        and min_position_top_weight > 0.80
        and positional_top_matches
        and unmasked_acc == 1.0
        and causal_acc == 0.5
        and mask_blocks_future
    )
    return {
        "schema_version": 1,
        "order_test_samples": len(order_test),
        "future_test_samples": len(future_test),
        "position_bag_baseline_accuracy": position_bag_acc,
        "no_position_attention_accuracy": no_position_acc,
        "positional_attention_accuracy": positional_acc,
        "position_gain_over_best_baseline": positional_acc - max(position_bag_acc, no_position_acc),
        "position_min_top_weight": min_position_top_weight,
        "positional_top_matches_query": positional_top_matches,
        "unmasked_future_lookup_accuracy": unmasked_acc,
        "causal_masked_lookup_accuracy": causal_acc,
        "mask_blocks_future": mask_blocks_future,
        "order_trace_rows": order_trace_rows(order_test),
        "future_trace_rows": future_trace_rows(future_test),
        "boundary": "Pure-Python attention probes for positional lookup and causal masking. This explains two Transformer support mechanisms, not full Transformer training or language-model quality.",
        "run_status": "ok" if run_ok else "failed",
    }


def dumps_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    print(dumps_json(build_probe()))
