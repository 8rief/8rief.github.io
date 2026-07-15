#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import torch

from text_classification import (
    LABELS,
    PAD,
    UNK,
    checkpoint_payload,
    encode,
    evaluate,
    first_token_baseline,
    keyword_rule_baseline,
    make_loader,
    majority_baseline,
    max_batch_stats,
    reload_checkpoint,
    split_examples,
    tensor_sha256,
    train_model,
    write_confusion,
    write_history,
    write_predictions,
    write_report,
    build_vocab,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PyTorch text-classification lab probe.")
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reports = args.reports_dir
    if reports.exists():
        import shutil

        shutil.rmtree(reports)
    reports.mkdir(parents=True, exist_ok=True)

    splits = split_examples()
    vocab = build_vocab(splits["train"])
    model, history = train_model(splits["train"], splits["val"], vocab)
    loss_fn = torch.nn.CrossEntropyLoss()
    val_loader = make_loader(splits["val"], vocab, batch_size=9, shuffle=False, seed=20260713)
    test_loader = make_loader(splits["test"], vocab, batch_size=9, shuffle=False, seed=20260713)
    test_metrics = evaluate(model, test_loader, loss_fn)
    val_metrics = evaluate(model, val_loader, loss_fn)
    shape, pad_count = max_batch_stats(test_loader, vocab[PAD])

    checkpoint_path = reports / "checkpoint.pt"
    torch.save(checkpoint_payload(model, vocab, history, test_metrics), checkpoint_path)
    reloaded, reloaded_vocab, checkpoint = reload_checkpoint(checkpoint_path)
    reload_metrics = evaluate(reloaded, test_loader, loss_fn)
    checkpoint_reload_match = reload_metrics["predictions"] == test_metrics["predictions"]

    unknown_ids = encode("please investigate biometric token outage", vocab)
    unk_count = sum(1 for item in unknown_ids if item == vocab[UNK])
    unknown_batch = next(iter(make_loader([splits["test"][0]], vocab, batch_size=1, shuffle=False, seed=1)))
    reloaded.eval()
    with torch.no_grad():
        logits_hash = tensor_sha256(reloaded(unknown_batch.input_ids, unknown_batch.lengths))

    summary = {
        "train_samples": len(splits["train"]),
        "val_samples": len(splits["val"]),
        "test_samples": len(splits["test"]),
        "vocab_size": len(vocab),
        "pad_id": vocab[PAD],
        "unk_id": vocab[UNK],
        "max_batch_width": shape[1],
        "pad_token_count": pad_count,
        "majority_baseline_acc": majority_baseline(splits["test"]),
        "first_token_baseline_acc": first_token_baseline(splits["train"], splits["test"]),
        "keyword_rule_baseline_acc": keyword_rule_baseline(splits["test"]),
        "model_val_acc": val_metrics["accuracy"],
        "model_test_acc": test_metrics["accuracy"],
        "model_matches_keyword_rule": test_metrics["accuracy"] == keyword_rule_baseline(splits["test"]),
        "checkpoint_reload_match": checkpoint_reload_match,
        "unknown_token_count": unk_count,
        "unknown_inference_hash": logits_hash,
        "confusion_matrix": test_metrics["confusion"],
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "run_status": "ok",
    }
    write_history(reports / "training_history.csv", history)
    write_confusion(reports / "confusion_matrix.csv", test_metrics["confusion"])
    write_predictions(reports / "prediction_table.csv", test_metrics["predictions"])
    write_report(reports / "text_classification_report.md", summary)
    (reports / "vocab.json").write_text(json.dumps(reloaded_vocab, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (reports / "text_classification_probe.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    markers = [
        ("TRAIN_SAMPLES", summary["train_samples"]),
        ("VAL_SAMPLES", summary["val_samples"]),
        ("TEST_SAMPLES", summary["test_samples"]),
        ("VOCAB_SIZE", summary["vocab_size"]),
        ("PAD_ID", summary["pad_id"]),
        ("UNK_ID", summary["unk_id"]),
        ("MAX_BATCH_WIDTH", summary["max_batch_width"]),
        ("PAD_TOKEN_COUNT", summary["pad_token_count"]),
        ("MAJORITY_BASELINE_ACC", summary["majority_baseline_acc"]),
        ("FIRST_TOKEN_BASELINE_ACC", summary["first_token_baseline_acc"]),
        ("KEYWORD_RULE_BASELINE_ACC", summary["keyword_rule_baseline_acc"]),
        ("MODEL_VAL_ACC", summary["model_val_acc"]),
        ("MODEL_TEST_ACC", summary["model_test_acc"]),
        ("MODEL_MATCHES_KEYWORD_RULE", "yes" if summary["model_matches_keyword_rule"] else "no"),
        ("CONFUSION_DIAGONAL", ":".join(str(summary["confusion_matrix"][i][i]) for i in range(len(LABELS)))),
        ("CHECKPOINT_RELOAD_MATCH", "yes" if checkpoint_reload_match else "no"),
        ("UNKNOWN_TOKEN_COUNT", summary["unknown_token_count"]),
        ("RUN_STATUS", summary["run_status"]),
    ]
    for key, value in markers:
        if isinstance(value, float):
            print(f"{key}={value:.3f}")
        else:
            print(f"{key}={value}")
    print("deep_learning_pytorch_text_classification_lab_status=ok")


if __name__ == "__main__":
    main()
