#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

from cnn_from_scratch import build_probe, dumps_json


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def bool_word(value: bool) -> str:
    return "yes" if value else "no"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    probe = build_probe()
    (reports / "cnn_probe.json").write_text(dumps_json(probe) + "\n", encoding="utf-8")

    rows = probe["feature_rows"]
    with (reports / "feature_table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# CNN foundations probe report",
        "",
        f"- Train samples: {probe['train_samples']}",
        f"- Test samples: {probe['test_samples']}",
        f"- Held-out positions: {probe['held_out_positions']}",
        f"- Majority baseline accuracy: {percent(probe['majority_baseline_accuracy'])}",
        f"- Raw position-template accuracy: {percent(probe['raw_template_accuracy'])}",
        f"- Convolution feature accuracy: {percent(probe['conv_feature_accuracy'])}",
        f"- Shift generalization gain: {percent(probe['shift_generalization_gain'])}",
        f"- Vertical filter response ok: {bool_word(probe['vertical_filter_response_ok'])}",
        f"- Horizontal filter response ok: {bool_word(probe['horizontal_filter_response_ok'])}",
        "",
        "| sample | label | position | raw template | conv feature | vertical response | horizontal response |",
        "| --- | --- | ---: | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['label']} | {row['position']} | "
            f"{row['raw_template_prediction']} | {row['conv_prediction']} | "
            f"{row['vertical_response']} | {row['horizontal_response']} |"
        )
    lines += ["", f"Boundary: {probe['boundary']}", ""]
    (reports / "cnn_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"TRAIN_SAMPLES={probe['train_samples']}")
    print(f"TEST_SAMPLES={probe['test_samples']}")
    print(f"MAJORITY_BASELINE_ACC={probe['majority_baseline_accuracy']:.3f}")
    print(f"RAW_TEMPLATE_ACC={probe['raw_template_accuracy']:.3f}")
    print(f"CONV_FEATURE_ACC={probe['conv_feature_accuracy']:.3f}")
    print(f"SHIFT_GENERALIZATION_GAIN={probe['shift_generalization_gain']:.3f}")
    print(f"VERTICAL_FILTER_RESPONSE_OK={bool_word(probe['vertical_filter_response_ok'])}")
    print(f"HORIZONTAL_FILTER_RESPONSE_OK={bool_word(probe['horizontal_filter_response_ok'])}")
    print(f"RUN_STATUS={probe['run_status']}")
    return 0 if probe["run_status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
