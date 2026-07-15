#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import torch

from training_engineering import (
    build_splits,
    checkpoint_logits_match,
    config_hash,
    config_to_dict,
    format_marker,
    majority_baseline_accuracy,
    read_config,
    reset_reports_dir,
    run_training,
    state_dicts_allclose,
    write_artifact_manifest,
    write_model_card,
    write_prediction_table,
    x_only_heuristic_accuracy,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PyTorch training-engineering lab probe.")
    parser.add_argument("--config", type=Path, default=Path("config/training_config.json"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--device", default=None, help="Override config device. CPU is recommended for deterministic evidence.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    if args.device is not None:
        config = type(config)(**{**config_to_dict(config), "device": args.device})
    if config.device != "cpu":
        raise SystemExit("This lab intentionally runs on CPU for deterministic evidence; set --device cpu.")

    reports_dir = args.reports_dir
    reset_reports_dir(reports_dir)
    splits = build_splits(config)

    majority_acc = majority_baseline_accuracy(splits["test"])
    heuristic_acc = x_only_heuristic_accuracy(splits["test"])
    full = run_training(config=config, splits=splits, reports_dir=reports_dir, run_id="full")
    checkpoint_epoch_path = Path(full["checkpoint_epoch_path"])
    resumed = run_training(
        config=config,
        splits=splits,
        reports_dir=reports_dir,
        run_id="resume",
        resume_checkpoint=checkpoint_epoch_path,
    )

    full_final = Path(full["final_path"])
    resume_final = Path(resumed["final_path"])
    resume_matches = state_dicts_allclose(full_final, resume_final)
    best_path = Path(full["best_path"])
    best_reload_match = checkpoint_logits_match(best_path, config, splits["test"])

    final_val_acc = full["final_metrics"]["val"]["accuracy"]
    final_test_acc = full["final_metrics"]["test"]["accuracy"]
    event_rows = sum(1 for path in reports_dir.glob("*_events.jsonl") for _ in path.open(encoding="utf-8"))

    # Load final model through the checkpoint to produce a human-readable prediction table.
    checkpoint = torch.load(full_final, map_location="cpu", weights_only=True)
    from training_engineering import TinyLinearClassifier  # local import keeps the top imports focused on the public API

    model = TinyLinearClassifier()
    model.load_state_dict(checkpoint["model_state_dict"])
    write_prediction_table(reports_dir / "test_predictions.csv", model, splits["test"])

    summary = {
        "task_name": config.task_name,
        "config_hash": config_hash(config),
        "config_hash_match": checkpoint["config_hash"] == config_hash(config),
        "train_samples": splits["train"].size,
        "val_samples": splits["val"].size,
        "test_samples": splits["test"].size,
        "majority_baseline_acc": majority_acc,
        "heuristic_baseline_acc": heuristic_acc,
        "final_val_acc": final_val_acc,
        "final_test_acc": final_test_acc,
        "best_checkpoint_reload_match": best_reload_match,
        "resume_matches_full_run": resume_matches,
        "jsonl_log_rows": event_rows,
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "run_status": "ok",
    }

    write_model_card(reports_dir / "model_card.md", config=config, summary=summary)
    manifest = write_artifact_manifest(
        reports_dir / "artifact_manifest.json",
        reports_dir,
        ["*.json", "*.jsonl", "*.csv", "*.md", "checkpoints/*.pt"],
    )
    summary["artifact_manifest_ready"] = manifest["artifact_count"] >= 6
    summary["model_card_ready"] = (reports_dir / "model_card.md").is_file()
    summary["artifact_manifest_count"] = manifest["artifact_count"]
    (reports_dir / "training_engineering_probe.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    markers = [
        ("CONFIG_HASH_MATCH", "yes" if summary["config_hash_match"] else "no"),
        ("TRAIN_SAMPLES", summary["train_samples"]),
        ("VAL_SAMPLES", summary["val_samples"]),
        ("TEST_SAMPLES", summary["test_samples"]),
        ("MAJORITY_BASELINE_ACC", majority_acc),
        ("HEURISTIC_BASELINE_ACC", heuristic_acc),
        ("FINAL_VAL_ACC", final_val_acc),
        ("FINAL_TEST_ACC", final_test_acc),
        ("BEST_CHECKPOINT_RELOAD_MATCH", "yes" if best_reload_match else "no"),
        ("RESUME_MATCHES_FULL_RUN", "yes" if resume_matches else "no"),
        ("JSONL_LOG_ROWS", event_rows),
        ("MODEL_CARD_READY", "yes" if summary["model_card_ready"] else "no"),
        ("ARTIFACT_MANIFEST_READY", "yes" if summary["artifact_manifest_ready"] else "no"),
        ("RUN_STATUS", summary["run_status"]),
    ]
    for key, value in markers:
        print(format_marker(key, value))
    print("deep_learning_pytorch_training_engineering_lab_status=ok")


if __name__ == "__main__":
    main()
