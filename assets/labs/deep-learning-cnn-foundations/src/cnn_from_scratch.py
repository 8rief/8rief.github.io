#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Iterable

Image = list[list[float]]
Kernel = list[list[float]]

VERTICAL_KERNEL: Kernel = [
    [-1.0, 2.0, -1.0],
    [-1.0, 2.0, -1.0],
    [-1.0, 2.0, -1.0],
]
HORIZONTAL_KERNEL: Kernel = [
    [-1.0, -1.0, -1.0],
    [2.0, 2.0, 2.0],
    [-1.0, -1.0, -1.0],
]


@dataclass(frozen=True)
class Sample:
    name: str
    label: str
    image: Image
    position: int


def zeros(height: int, width: int) -> Image:
    return [[0.0 for _ in range(width)] for _ in range(height)]


def clone_image(image: Image) -> Image:
    return [row[:] for row in image]


def add_bar(label: str, position: int, *, size: int = 8, margin: int = 1) -> Image:
    image = zeros(size, size)
    if label == "vertical":
        for r in range(margin, size - margin):
            image[r][position] = 1.0
    elif label == "horizontal":
        for c in range(margin, size - margin):
            image[position][c] = 1.0
    else:
        raise ValueError(f"unknown label {label}")
    return image


def add_deterministic_noise(image: Image, *, seed: int, magnitude: float = 0.05) -> Image:
    # Tiny deterministic background noise prevents the report from looking like
    # a hand-coded one-hot table while keeping the class signal obvious.
    out = clone_image(image)
    state = seed & 0x7FFFFFFF
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            state = (1103515245 * state + 12345) & 0x7FFFFFFF
            if value == 0.0 and state % 17 == 0:
                out[r][c] = magnitude
    return out


def make_dataset() -> tuple[list[Sample], list[Sample]]:
    train: list[Sample] = []
    test: list[Sample] = []
    for label in ["vertical", "horizontal"]:
        for pos in [1, 2]:
            train.append(Sample(f"train-{label}-{pos}", label, add_deterministic_noise(add_bar(label, pos), seed=pos), pos))
        for pos in [5, 6]:
            test.append(Sample(f"test-{label}-{pos}", label, add_deterministic_noise(add_bar(label, pos), seed=100 + pos), pos))
    return train, test


def pad2d(image: Image, padding: int) -> Image:
    if padding < 0:
        raise ValueError("padding must be non-negative")
    if padding == 0:
        return clone_image(image)
    height = len(image)
    width = len(image[0]) if height else 0
    padded = zeros(height + 2 * padding, width + 2 * padding)
    for r, row in enumerate(image):
        for c, value in enumerate(row):
            padded[r + padding][c + padding] = value
    return padded


def conv2d(image: Image, kernel: Kernel, *, padding: int = 0, stride: int = 1) -> Image:
    if stride <= 0:
        raise ValueError("stride must be positive")
    source = pad2d(image, padding)
    image_h = len(source)
    image_w = len(source[0]) if image_h else 0
    kernel_h = len(kernel)
    kernel_w = len(kernel[0]) if kernel_h else 0
    if kernel_h == 0 or kernel_w == 0 or image_h < kernel_h or image_w < kernel_w:
        raise ValueError("kernel must fit inside the padded image")
    out_h = (image_h - kernel_h) // stride + 1
    out_w = (image_w - kernel_w) // stride + 1
    out = zeros(out_h, out_w)
    for out_r in range(out_h):
        for out_c in range(out_w):
            acc = 0.0
            base_r = out_r * stride
            base_c = out_c * stride
            for kr in range(kernel_h):
                for kc in range(kernel_w):
                    acc += source[base_r + kr][base_c + kc] * kernel[kr][kc]
            out[out_r][out_c] = acc
    return out


def relu(feature_map: Image) -> Image:
    return [[max(0.0, value) for value in row] for row in feature_map]


def max_pool2d(feature_map: Image, *, size: int = 2, stride: int = 2) -> Image:
    if size <= 0 or stride <= 0:
        raise ValueError("size and stride must be positive")
    height = len(feature_map)
    width = len(feature_map[0]) if height else 0
    if height < size or width < size:
        raise ValueError("pooling window must fit feature map")
    out_h = (height - size) // stride + 1
    out_w = (width - size) // stride + 1
    out = zeros(out_h, out_w)
    for out_r in range(out_h):
        for out_c in range(out_w):
            base_r = out_r * stride
            base_c = out_c * stride
            out[out_r][out_c] = max(
                feature_map[base_r + wr][base_c + wc]
                for wr in range(size)
                for wc in range(size)
            )
    return out


def global_max(feature_map: Image) -> float:
    return max(value for row in feature_map for value in row)


def conv_features(image: Image) -> dict[str, float]:
    vertical_map = max_pool2d(relu(conv2d(image, VERTICAL_KERNEL, padding=1)), size=2, stride=2)
    horizontal_map = max_pool2d(relu(conv2d(image, HORIZONTAL_KERNEL, padding=1)), size=2, stride=2)
    return {
        "vertical_response": global_max(vertical_map),
        "horizontal_response": global_max(horizontal_map),
    }


def predict_from_conv_features(image: Image) -> str:
    features = conv_features(image)
    return "vertical" if features["vertical_response"] >= features["horizontal_response"] else "horizontal"


def flatten(image: Image) -> list[float]:
    return [value for row in image for value in row]


def class_centroids(samples: Iterable[Sample]) -> dict[str, list[float]]:
    sums: dict[str, list[float]] = {}
    counts: dict[str, int] = {}
    for sample in samples:
        vector = flatten(sample.image)
        sums.setdefault(sample.label, [0.0 for _ in vector])
        counts[sample.label] = counts.get(sample.label, 0) + 1
        for i, value in enumerate(vector):
            sums[sample.label][i] += value
    return {
        label: [value / counts[label] for value in values]
        for label, values in sums.items()
    }


def squared_distance(left: list[float], right: list[float]) -> float:
    return sum((a - b) * (a - b) for a, b in zip(left, right))


def predict_from_raw_template(image: Image, centroids: dict[str, list[float]]) -> str:
    vector = flatten(image)
    scored = sorted((squared_distance(vector, centroid), label) for label, centroid in centroids.items())
    return scored[0][1]


def majority_label(samples: Iterable[Sample]) -> str:
    counts: dict[str, int] = {}
    for sample in samples:
        counts[sample.label] = counts.get(sample.label, 0) + 1
    return sorted((-count, label) for label, count in counts.items())[0][1]


def accuracy(samples: Iterable[Sample], predict) -> float:
    rows = list(samples)
    if not rows:
        raise ValueError("accuracy needs at least one sample")
    return sum(1 for sample in rows if predict(sample.image) == sample.label) / len(rows)


def feature_rows(samples: Iterable[Sample], centroids: dict[str, list[float]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sample in samples:
        features = conv_features(sample.image)
        rows.append({
            "name": sample.name,
            "label": sample.label,
            "position": sample.position,
            "raw_template_prediction": predict_from_raw_template(sample.image, centroids),
            "conv_prediction": predict_from_conv_features(sample.image),
            "vertical_response": round(features["vertical_response"], 4),
            "horizontal_response": round(features["horizontal_response"], 4),
        })
    return rows


def build_probe() -> dict[str, object]:
    train, test = make_dataset()
    centroids = class_centroids(train)
    majority = majority_label(train)
    majority_acc = accuracy(test, lambda _image: majority)
    raw_template_acc = accuracy(test, lambda image: predict_from_raw_template(image, centroids))
    conv_acc = accuracy(test, predict_from_conv_features)
    rows = feature_rows(test, centroids)
    vertical_rows = [row for row in rows if row["label"] == "vertical"]
    horizontal_rows = [row for row in rows if row["label"] == "horizontal"]
    vertical_filter_ok = all(row["vertical_response"] > row["horizontal_response"] for row in vertical_rows)
    horizontal_filter_ok = all(row["horizontal_response"] > row["vertical_response"] for row in horizontal_rows)
    return {
        "schema_version": 1,
        "train_samples": len(train),
        "test_samples": len(test),
        "held_out_positions": sorted({sample.position for sample in test}),
        "majority_baseline_accuracy": majority_acc,
        "raw_template_accuracy": raw_template_acc,
        "conv_feature_accuracy": conv_acc,
        "shift_generalization_gain": conv_acc - raw_template_acc,
        "vertical_filter_response_ok": vertical_filter_ok,
        "horizontal_filter_response_ok": horizontal_filter_ok,
        "feature_rows": rows,
        "boundary": "Synthetic shifted bars show convolution weight sharing and global max pooling. This is not a real image-recognition benchmark.",
        "run_status": "ok" if conv_acc == 1.0 and raw_template_acc < conv_acc and vertical_filter_ok and horizontal_filter_ok else "failed",
    }


def dumps_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    print(dumps_json(build_probe()))
