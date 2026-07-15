#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import torch
from torch import nn

from inference_boundary import (
    InferenceDemoNet,
    benchmark_inference,
    check_mode_boundaries,
    compare_single_vs_batch,
    evaluate,
    make_examples,
    make_loader,
    majority_baseline_accuracy,
    predict_table,
    save_history,
    save_predictions,
    sha256_file,
    train_model,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def fmt(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    splits = make_examples()
    model, history = train_model(splits["train"], splits["val"])
    loss_fn = nn.CrossEntropyLoss()
    test_loader = make_loader(splits["test"], batch_size=128, shuffle=False, seed=20260714)
    test_metrics = evaluate(model, test_loader, loss_fn)
    baseline = majority_baseline_accuracy(splits["train"], splits["test"])

    checkpoint_path = REPORTS / "checkpoint.pt"
    torch.save({"model_state_dict": model.state_dict(), "input_dim": 2, "labels": [0, 1]}, checkpoint_path)
    checkpoint_hash = sha256_file(checkpoint_path)
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    reloaded = InferenceDemoNet()
    reloaded.load_state_dict(payload["model_state_dict"])
    reloaded_metrics = evaluate(reloaded, test_loader, loss_fn)
    checkpoint_reload_match = abs(reloaded_metrics["loss"] - test_metrics["loss"]) < 1e-9 and reloaded_metrics["accuracy"] == test_metrics["accuracy"]

    mode_checks = check_mode_boundaries(reloaded, splits["test"][0])
    compare = compare_single_vs_batch(reloaded, splits["test"][:32])
    timing = benchmark_inference(reloaded, splits["test"][:128], repeats=40)
    predictions = predict_table(reloaded, test_loader)
    prediction_accuracy = sum(int(row["gold"] == row["pred"]) for row in predictions) / len(predictions)

    probe = {
        "run_status": "ok",
        "train_samples": len(splits["train"]),
        "val_samples": len(splits["val"]),
        "test_samples": len(splits["test"]),
        "majority_baseline_acc": baseline,
        "test_acc": test_metrics["accuracy"],
        "test_loss": test_metrics["loss"],
        "prediction_table_acc": prediction_accuracy,
        "checkpoint_hash": checkpoint_hash,
        "checkpoint_reload_match": checkpoint_reload_match,
        "mode_checks": mode_checks,
        "single_vs_batch": compare,
        "timing": timing,
        "device": "cpu",
        "timing_boundary": "CPU perf_counter with warmup; toy local timing only",
    }
    if probe["test_acc"] < 0.97:
        raise AssertionError(f"test accuracy too low: {probe['test_acc']}")
    if probe["test_acc"] <= baseline:
        raise AssertionError("model did not beat majority baseline")
    if not checkpoint_reload_match:
        raise AssertionError("checkpoint reload changed metrics")
    if not mode_checks["train_mode_output_changed"]:
        raise AssertionError("train mode dropout did not change output")
    if not mode_checks["eval_output_stable"]:
        raise AssertionError("eval output is not stable")
    if mode_checks["inference_requires_grad"]:
        raise AssertionError("inference output unexpectedly requires grad")
    if not mode_checks["inference_mode_enabled_inside"]:
        raise AssertionError("inference mode flag was not enabled")
    if not compare["batch_output_match"]:
        raise AssertionError("batch and single inference outputs differ")
    if timing["batch_per_sample_us"] <= 0 or timing["single_per_sample_us"] <= 0:
        raise AssertionError("timing values must be positive")

    (REPORTS / "inference_probe.json").write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")
    save_history(REPORTS / "training_history.csv", history)
    save_predictions(REPORTS / "predictions.csv", predictions)
    manifest = {
        "checkpoint": {"path": "reports/checkpoint.pt", "sha256": checkpoint_hash},
        "prediction_rows": len(predictions),
        "report_files": ["inference_probe.json", "training_history.csv", "predictions.csv", "inference_report.md"],
    }
    (REPORTS / "artifact_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report = "\n".join(
        [
            "# PyTorch inference-boundary probe report",
            "",
            f"Train/val/test: {len(splits['train'])}/{len(splits['val'])}/{len(splits['test'])}",
            f"Majority baseline accuracy: {fmt(baseline)}",
            f"Model test accuracy: {fmt(test_metrics['accuracy'])}",
            f"Checkpoint reload match: {'yes' if checkpoint_reload_match else 'no'}",
            f"Train-mode output changed: {'yes' if mode_checks['train_mode_output_changed'] else 'no'}",
            f"Eval output stable: {'yes' if mode_checks['eval_output_stable'] else 'no'}",
            f"Batch output match: {'yes' if compare['batch_output_match'] else 'no'}",
            f"Batch per sample: {timing['batch_per_sample_us']:.2f} us",
            f"Single per sample: {timing['single_per_sample_us']:.2f} us",
            "",
            "Boundary: timing is a local CPU smoke measurement, not a production benchmark.",
        ]
    )
    (REPORTS / "inference_report.md").write_text(report + "\n", encoding="utf-8")

    markers = {
        "TRAIN_SAMPLES": len(splits["train"]),
        "VAL_SAMPLES": len(splits["val"]),
        "TEST_SAMPLES": len(splits["test"]),
        "MAJORITY_BASELINE_ACC": fmt(baseline),
        "MODEL_TEST_ACC": fmt(test_metrics["accuracy"]),
        "MODEL_BEATS_BASELINE": "yes" if test_metrics["accuracy"] > baseline else "no",
        "TRAIN_MODE_OUTPUT_CHANGED": "yes" if mode_checks["train_mode_output_changed"] else "no",
        "EVAL_OUTPUT_STABLE": "yes" if mode_checks["eval_output_stable"] else "no",
        "INFERENCE_MODE_ENABLED_INSIDE": "yes" if mode_checks["inference_mode_enabled_inside"] else "no",
        "INFERENCE_REQUIRES_GRAD": "yes" if mode_checks["inference_requires_grad"] else "no",
        "BATCH_OUTPUT_MATCH": "yes" if compare["batch_output_match"] else "no",
        "BATCH_TIMING_RECORDED": "yes" if timing["batch_per_sample_us"] > 0 else "no",
        "CHECKPOINT_RELOAD_MATCH": "yes" if checkpoint_reload_match else "no",
        "PREDICTION_TABLE_ROWS": len(predictions),
        "RUN_STATUS": "ok",
    }
    for key, value in markers.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
