#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

Vector = tuple[float, ...]
Label = str

COLORS = {"A": -1.0, "B": 1.0}
SHAPES = {"X": -1.0, "Y": 1.0}
POSITION_SCALE = 3.0


@dataclass(frozen=True)
class PairSample:
    name: str
    color: str
    shape: str
    label: Label


@dataclass(frozen=True)
class BlockSample:
    name: str
    local: str
    context: str
    label: Label


def label_from_codes(color_code: float, shape_code: float) -> Label:
    color = "B" if color_code > 0 else "A"
    shape = "Y" if shape_code > 0 else "X"
    return f"{color}|{shape}"


def dot(left: Vector, right: Vector) -> float:
    if len(left) != len(right):
        raise ValueError("dot product needs equal vector sizes")
    return sum(a * b for a, b in zip(left, right))


def add(left: Vector, right: Vector) -> Vector:
    if len(left) != len(right):
        raise ValueError("add needs equal vector sizes")
    return tuple(a + b for a, b in zip(left, right))


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


def position_vector(position: int, size: int) -> Vector:
    if not 0 <= position < size:
        raise ValueError("position out of range")
    return tuple(POSITION_SCALE if index == position else 0.0 for index in range(size))


def scaled_dot_product_attention(query: Vector, keys: list[Vector], values: list[Vector]) -> tuple[Vector, list[float], list[float]]:
    if len(keys) != len(values):
        raise ValueError("key/value count mismatch")
    if not keys:
        raise ValueError("attention needs at least one slot")
    scale = 1.0 / math.sqrt(len(query))
    scores = [dot(query, key) * scale for key in keys]
    weights = softmax(scores)
    return weighted_sum(weights, values), weights, scores


def layer_norm(vector: Vector, eps: float = 1e-12) -> Vector:
    if not vector:
        raise ValueError("layer_norm needs a vector")
    mean = sum(vector) / len(vector)
    variance = sum((value - mean) ** 2 for value in vector) / len(vector)
    scale = math.sqrt(variance + eps)
    return tuple((value - mean) / scale for value in vector)


def rms(vector: Vector) -> float:
    return math.sqrt(sum(value * value for value in vector) / len(vector))


def make_pair_dataset() -> tuple[list[PairSample], list[PairSample]]:
    base = [
        PairSample("pair-ax", "A", "X", "A|X"),
        PairSample("pair-ay", "A", "Y", "A|Y"),
        PairSample("pair-bx", "B", "X", "B|X"),
        PairSample("pair-by", "B", "Y", "B|Y"),
    ]
    train = [PairSample(f"train-{rep}-{sample.name}", sample.color, sample.shape, sample.label) for rep in range(2) for sample in base]
    test = [PairSample(f"test-{rep}-{sample.name}", sample.color, sample.shape, sample.label) for rep in range(2) for sample in reversed(base)]
    return train, test


def make_block_dataset() -> tuple[list[BlockSample], list[BlockSample]]:
    base = [
        BlockSample("block-ax", "A", "X", "A|X"),
        BlockSample("block-ay", "A", "Y", "A|Y"),
        BlockSample("block-bx", "B", "X", "B|X"),
        BlockSample("block-by", "B", "Y", "B|Y"),
    ]
    train = [BlockSample(f"train-{rep}-{sample.name}", sample.local, sample.context, sample.label) for rep in range(2) for sample in base]
    test = [BlockSample(f"test-{rep}-{sample.name}", sample.local, sample.context, sample.label) for rep in range(2) for sample in reversed(base)]
    return train, test


def accuracy(samples: Iterable[object], predict: Callable[[object], Label]) -> float:
    rows = list(samples)
    if not rows:
        raise ValueError("accuracy needs samples")
    return sum(1 for sample in rows if predict(sample) == sample.label) / len(rows)  # type: ignore[attr-defined]


def best_scalar_lookup(train: Iterable[PairSample], score_fn: Callable[[PairSample], float]) -> dict[float, Label]:
    buckets: dict[float, Counter[str]] = defaultdict(Counter)
    for sample in train:
        buckets[round(score_fn(sample), 6)][sample.label] += 1
    mapping: dict[float, Label] = {}
    for score, counts in buckets.items():
        mapping[score] = sorted((-count, label) for label, count in counts.items())[0][1]
    return mapping


def pair_keys() -> list[Vector]:
    return [position_vector(index, 4) for index in range(4)]


def color_values(sample: PairSample) -> list[Vector]:
    return [(COLORS[sample.color],), (0.0,), (0.0,), (0.0,)]


def shape_values(sample: PairSample) -> list[Vector]:
    return [(0.0,), (0.0,), (SHAPES[sample.shape],), (0.0,)]


def blended_values(sample: PairSample) -> list[Vector]:
    return [(COLORS[sample.color],), (0.0,), (SHAPES[sample.shape],), (0.0,)]


def single_first_head_trace(sample: PairSample) -> dict[str, object]:
    output, weights, scores = scaled_dot_product_attention(position_vector(0, 4), pair_keys(), color_values(sample))
    return {"score": output[0], "weights": weights, "scores": scores, "prediction": label_from_codes(output[0], -1.0)}


def predict_single_first_head(sample: PairSample) -> Label:
    return str(single_first_head_trace(sample)["prediction"])


def single_second_head_trace(sample: PairSample) -> dict[str, object]:
    output, weights, scores = scaled_dot_product_attention(position_vector(2, 4), pair_keys(), shape_values(sample))
    return {"score": output[0], "weights": weights, "scores": scores, "prediction": label_from_codes(-1.0, output[0])}


def predict_single_second_head(sample: PairSample) -> Label:
    return str(single_second_head_trace(sample)["prediction"])


def single_blend_score(sample: PairSample) -> float:
    query = add(position_vector(0, 4), position_vector(2, 4))
    output, _weights, _scores = scaled_dot_product_attention(query, pair_keys(), blended_values(sample))
    return output[0]


def make_blend_predictor(train: Iterable[PairSample]) -> Callable[[PairSample], Label]:
    mapping = best_scalar_lookup(train, single_blend_score)

    def predict(sample: PairSample) -> Label:
        return mapping[round(single_blend_score(sample), 6)]

    return predict


def single_blend_trace(sample: PairSample, train: Iterable[PairSample]) -> dict[str, object]:
    query = add(position_vector(0, 4), position_vector(2, 4))
    output, weights, scores = scaled_dot_product_attention(query, pair_keys(), blended_values(sample))
    prediction = make_blend_predictor(train)(sample)
    return {"score": output[0], "weights": weights, "scores": scores, "prediction": prediction}


def multi_head_pair_trace(sample: PairSample) -> dict[str, object]:
    color_output, color_weights, color_scores = scaled_dot_product_attention(position_vector(0, 4), pair_keys(), color_values(sample))
    shape_output, shape_weights, shape_scores = scaled_dot_product_attention(position_vector(2, 4), pair_keys(), shape_values(sample))
    prediction = label_from_codes(color_output[0], shape_output[0])
    return {
        "color_score": color_output[0],
        "shape_score": shape_output[0],
        "color_weights": color_weights,
        "shape_weights": shape_weights,
        "color_scores": color_scores,
        "shape_scores": shape_scores,
        "prediction": prediction,
        "color_top_position": max(range(4), key=lambda i: color_weights[i]),
        "shape_top_position": max(range(4), key=lambda i: shape_weights[i]),
    }


def predict_multi_head_pair(sample: PairSample) -> Label:
    return str(multi_head_pair_trace(sample)["prediction"])


def balanced_local_vector(local: str) -> Vector:
    code = COLORS[local]
    return (code, -code, 0.0, 0.0)


def balanced_context_vector(context: str) -> Vector:
    code = SHAPES[context]
    return (0.0, 0.0, code, -code)


def block_attention_context(sample: BlockSample) -> tuple[Vector, list[float], list[float]]:
    keys = [position_vector(index, 3) for index in range(3)]
    values = [(0.0, 0.0, 0.0, 0.0), balanced_context_vector(sample.context), (0.0, 0.0, 0.0, 0.0)]
    return scaled_dot_product_attention(position_vector(1, 3), keys, values)


def no_attention_block_trace(sample: BlockSample) -> dict[str, object]:
    vector = balanced_local_vector(sample.local)
    prediction = label_from_codes(vector[0], -1.0)
    return {"vector": vector, "prediction": prediction}


def predict_no_attention_block(sample: BlockSample) -> Label:
    return str(no_attention_block_trace(sample)["prediction"])


def no_residual_block_trace(sample: BlockSample) -> dict[str, object]:
    context, weights, scores = block_attention_context(sample)
    prediction = label_from_codes(-1.0, context[2])
    return {"vector": context, "weights": weights, "scores": scores, "prediction": prediction}


def predict_no_residual_block(sample: BlockSample) -> Label:
    return str(no_residual_block_trace(sample)["prediction"])


def position_wise_feed_forward_classifier(vector: Vector) -> Label:
    if len(vector) != 4:
        raise ValueError("classifier expects four features")
    return label_from_codes(vector[0] - vector[1], vector[2] - vector[3])


def transformer_block_trace(sample: BlockSample) -> dict[str, object]:
    residual = balanced_local_vector(sample.local)
    context, weights, scores = block_attention_context(sample)
    mixed = add(residual, context)
    normalized = layer_norm(mixed)
    prediction = position_wise_feed_forward_classifier(normalized)
    return {
        "residual": residual,
        "attention_context": context,
        "mixed": mixed,
        "normalized": normalized,
        "weights": weights,
        "scores": scores,
        "prediction": prediction,
        "norm_mean": sum(normalized) / len(normalized),
        "norm_rms": rms(normalized),
    }


def predict_transformer_block(sample: BlockSample) -> Label:
    return str(transformer_block_trace(sample)["prediction"])


def build_probe() -> dict[str, object]:
    pair_train, pair_test = make_pair_dataset()
    block_train, block_test = make_block_dataset()
    blend_predict = make_blend_predictor(pair_train)
    single_first = accuracy(pair_test, predict_single_first_head)
    single_second = accuracy(pair_test, predict_single_second_head)
    single_blend = accuracy(pair_test, blend_predict)
    multi_head = accuracy(pair_test, predict_multi_head_pair)
    no_attention = accuracy(block_test, predict_no_attention_block)
    no_residual = accuracy(block_test, predict_no_residual_block)
    block = accuracy(block_test, predict_transformer_block)
    head_traces = [multi_head_pair_trace(sample) for sample in pair_test]
    block_traces = [transformer_block_trace(sample) for sample in block_test]
    min_head_top_weight = min(
        min(float(trace["color_weights"][int(trace["color_top_position"])]), float(trace["shape_weights"][int(trace["shape_top_position"])]))
        for trace in head_traces
    )
    heads_focus_different = all(trace["color_top_position"] == 0 and trace["shape_top_position"] == 2 for trace in head_traces)
    norm_mean_ok = all(abs(float(trace["norm_mean"])) < 1e-9 for trace in block_traces)
    norm_rms_ok = all(abs(float(trace["norm_rms"]) - 1.0) < 1e-9 for trace in block_traces)
    return {
        "pair_test_samples": len(pair_test),
        "block_test_samples": len(block_test),
        "single_first_head_accuracy": single_first,
        "single_second_head_accuracy": single_second,
        "single_blend_head_accuracy": single_blend,
        "multi_head_pair_accuracy": multi_head,
        "multi_head_gain_over_best_baseline": multi_head - max(single_first, single_second, single_blend),
        "multi_head_min_top_weight": min_head_top_weight,
        "heads_focus_different_keys": heads_focus_different,
        "no_attention_block_accuracy": no_attention,
        "no_residual_block_accuracy": no_residual,
        "attention_residual_ffn_accuracy": block,
        "block_gain_over_best_baseline": block - max(no_attention, no_residual),
        "layer_norm_mean_ok": norm_mean_ok,
        "layer_norm_rms_ok": norm_rms_ok,
        "run_status": "ok",
    }


def multi_head_trace_rows(samples: Iterable[PairSample], train: Iterable[PairSample]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    train_rows = list(train)
    for sample in samples:
        first = single_first_head_trace(sample)
        second = single_second_head_trace(sample)
        blend = single_blend_trace(sample, train_rows)
        multi = multi_head_pair_trace(sample)
        rows.append({
            "name": sample.name,
            "label": sample.label,
            "single_first": first["prediction"],
            "single_second": second["prediction"],
            "single_blend": blend["prediction"],
            "multi_head": multi["prediction"],
            "blend_score": round(float(blend["score"]), 6),
            "color_top": multi["color_top_position"],
            "shape_top": multi["shape_top_position"],
        })
    return rows


def block_trace_rows(samples: Iterable[BlockSample]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sample in samples:
        no_attn = no_attention_block_trace(sample)
        no_resid = no_residual_block_trace(sample)
        block = transformer_block_trace(sample)
        rows.append({
            "name": sample.name,
            "label": sample.label,
            "no_attention": no_attn["prediction"],
            "no_residual": no_resid["prediction"],
            "block": block["prediction"],
            "norm_mean": round(float(block["norm_mean"]), 6),
            "norm_rms": round(float(block["norm_rms"]), 6),
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write empty csv")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_probe_reports(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    pair_train, pair_test = make_pair_dataset()
    _block_train, block_test = make_block_dataset()
    probe = build_probe()
    (root / "transformer_block_probe.json").write_text(json.dumps(probe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(root / "multi_head_trace_table.csv", multi_head_trace_rows(pair_test, pair_train))
    write_csv(root / "block_trace_table.csv", block_trace_rows(block_test))
    report = [
        "# Transformer multi-head/block probe",
        "",
        f"- pair test samples: {probe['pair_test_samples']}",
        f"- block test samples: {probe['block_test_samples']}",
        f"- single first-head accuracy: {probe['single_first_head_accuracy']:.3f}",
        f"- single second-head accuracy: {probe['single_second_head_accuracy']:.3f}",
        f"- single blended-head accuracy: {probe['single_blend_head_accuracy']:.3f}",
        f"- multi-head pair accuracy: {probe['multi_head_pair_accuracy']:.3f}",
        f"- no-attention block accuracy: {probe['no_attention_block_accuracy']:.3f}",
        f"- no-residual block accuracy: {probe['no_residual_block_accuracy']:.3f}",
        f"- attention+residual+FFN accuracy: {probe['attention_residual_ffn_accuracy']:.3f}",
        f"- run status: {probe['run_status']}",
        "",
    ]
    (root / "transformer_block_report.md").write_text("\n".join(report), encoding="utf-8")
    return probe
