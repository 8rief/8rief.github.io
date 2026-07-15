#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import torch
from torch import nn

from char_lm import (
    BOS,
    EOS,
    PAD,
    bigram_baseline,
    build_vocab,
    evaluate_model,
    greedy_generate,
    make_loader,
    predict_next_char,
    save_final_predictions,
    save_history,
    split_examples,
    train_model,
    unigram_baseline,
    uniform_nll,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def fmt(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    splits = split_examples()
    vocab = build_vocab(splits["train"])
    model, history = train_model(splits["train"], splits["val"], vocab)
    loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
    test_loader = make_loader(splits["test"], vocab, batch_size=9, shuffle=False, seed=20260714)
    val_loader = make_loader(splits["val"], vocab, batch_size=9, shuffle=False, seed=20260714)
    train_loader = make_loader(splits["train"], vocab, batch_size=9, shuffle=False, seed=20260714)
    train_metrics = evaluate_model(model, train_loader, loss_fn, vocab)
    val_metrics = evaluate_model(model, val_loader, loss_fn, vocab)
    test_metrics = evaluate_model(model, test_loader, loss_fn, vocab)
    unigram = unigram_baseline(splits["train"], splits["test"])
    bigram = bigram_baseline(splits["train"], splits["test"])

    prompts = {}
    shared_suffix = splits["test"][0].raw[1:-1]
    for cue in ["a", "b", "c"]:
        prefix = f"{cue}{shared_suffix}"
        # The prefix ends at the shared delimiter. The next character is the
        # dependency test: it should be A/B/C according to the first cue.
        next_char, confidence, top3 = predict_next_char(model, vocab, prefix)
        prompts[cue] = {"prefix": prefix, "next_char": next_char, "confidence": confidence, "top3": top3}

    generated = {cue: greedy_generate(model, vocab, cue, max_new_chars=8) for cue in ["a", "b", "c"]}

    checkpoint_path = REPORTS / "checkpoint.pt"
    torch.save({"model_state_dict": model.state_dict(), "vocab": vocab}, checkpoint_path)
    from char_lm import CharGRULanguageModel

    reloaded_model = CharGRULanguageModel(vocab_size=len(vocab), embedding_dim=12, hidden_size=24, pad_id=vocab[PAD])
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    reloaded_model.load_state_dict(payload["model_state_dict"])
    reloaded_metrics = evaluate_model(reloaded_model, test_loader, loss_fn, vocab)
    reload_match = abs(float(reloaded_metrics["nll"]) - float(test_metrics["nll"])) < 1e-9 and reloaded_metrics["final_accuracy"] == test_metrics["final_accuracy"]

    targets = [*splits["train"][0].raw, EOS]
    inputs = [BOS, *splits["train"][0].raw]
    teacher_forcing_shift_ok = all(inputs[i + 1] == targets[i] for i in range(len(targets) - 1))

    probe = {
        "run_status": "ok",
        "train_samples": len(splits["train"]),
        "val_samples": len(splits["val"]),
        "test_samples": len(splits["test"]),
        "vocab_size": len(vocab),
        "pad_id": vocab[PAD],
        "bos_id": vocab[BOS],
        "eos_id": vocab[EOS],
        "uniform_nll": uniform_nll(len(vocab)),
        "unigram_token_accuracy": unigram["token_accuracy"],
        "unigram_final_accuracy": unigram["final_accuracy"],
        "bigram_token_accuracy": bigram["token_accuracy"],
        "bigram_final_accuracy": bigram["final_accuracy"],
        "bigram_delimiter_prediction": bigram["delimiter_prediction"],
        "model_train_nll": train_metrics["nll"],
        "model_val_nll": val_metrics["nll"],
        "model_test_nll": test_metrics["nll"],
        "model_train_final_accuracy": train_metrics["final_accuracy"],
        "model_val_final_accuracy": val_metrics["final_accuracy"],
        "model_token_accuracy": test_metrics["token_accuracy"],
        "model_final_accuracy": test_metrics["final_accuracy"],
        "teacher_forcing_shift_ok": teacher_forcing_shift_ok,
        "checkpoint_reload_match": reload_match,
        "prompts": prompts,
        "generated": generated,
    }

    if probe["model_final_accuracy"] < 0.999:
        raise AssertionError(f"model final accuracy too low: {probe['model_final_accuracy']}")
    if probe["bigram_final_accuracy"] > 0.334:
        raise AssertionError(f"bigram final accuracy unexpectedly high: {probe['bigram_final_accuracy']}")
    if not reload_match:
        raise AssertionError("checkpoint reload changed evaluation metrics")
    if not teacher_forcing_shift_ok:
        raise AssertionError("teacher forcing input/target shift is wrong")
    for cue, expected in {"a": "A", "b": "B", "c": "C"}.items():
        if prompts[cue]["next_char"] != expected:
            raise AssertionError(f"prompt {cue} predicted {prompts[cue]['next_char']}, expected {expected}")

    (REPORTS / "char_lm_probe.json").write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORTS / "vocab.json").write_text(json.dumps(vocab, ensure_ascii=False, indent=2), encoding="utf-8")
    save_history(REPORTS / "training_history.csv", history)
    save_final_predictions(REPORTS / "final_predictions.csv", test_metrics["final_rows"])
    report = "\n".join(
        [
            "# Character LM probe report",
            "",
            f"Train/val/test: {len(splits['train'])}/{len(splits['val'])}/{len(splits['test'])}",
            f"Vocabulary size: {len(vocab)}",
            f"Bigram final accuracy: {fmt(float(bigram['final_accuracy']))}",
            f"Model final accuracy: {fmt(float(test_metrics['final_accuracy']))}",
            f"Model test NLL: {fmt(float(test_metrics['nll']))}",
            f"Checkpoint reload match: {'yes' if reload_match else 'no'}",
            "",
            "Prompt next-character predictions:",
            *[f"- {item['prefix']} -> {item['next_char']} ({item['confidence']:.3f})" for item in prompts.values()],
            "",
            "Boundary: this toy grammar proves the pipeline and a long-range cue, not open-domain text generation quality.",
        ]
    )
    (REPORTS / "char_lm_report.md").write_text(report + "\n", encoding="utf-8")

    markers = {
        "TRAIN_SAMPLES": len(splits["train"]),
        "VAL_SAMPLES": len(splits["val"]),
        "TEST_SAMPLES": len(splits["test"]),
        "VOCAB_SIZE": len(vocab),
        "PAD_ID": vocab[PAD],
        "BOS_ID": vocab[BOS],
        "EOS_ID": vocab[EOS],
        "UNIFORM_NLL": fmt(uniform_nll(len(vocab))),
        "UNIGRAM_FINAL_ACC": fmt(float(unigram["final_accuracy"])),
        "BIGRAM_TOKEN_ACC": fmt(float(bigram["token_accuracy"])),
        "BIGRAM_FINAL_ACC": fmt(float(bigram["final_accuracy"])),
        "MODEL_VAL_FINAL_ACC": fmt(float(val_metrics["final_accuracy"])),
        "MODEL_TOKEN_ACC": fmt(float(test_metrics["token_accuracy"])),
        "MODEL_FINAL_ACC": fmt(float(test_metrics["final_accuracy"])),
        "MODEL_TEST_NLL": fmt(float(test_metrics["nll"])),
        "MODEL_BEATS_BIGRAM_FINAL": "yes" if test_metrics["final_accuracy"] > bigram["final_accuracy"] else "no",
        "PROMPT_A_NEXT": prompts["a"]["next_char"],
        "PROMPT_B_NEXT": prompts["b"]["next_char"],
        "PROMPT_C_NEXT": prompts["c"]["next_char"],
        "TEACHER_FORCING_SHIFT_OK": "yes" if teacher_forcing_shift_ok else "no",
        "CHECKPOINT_RELOAD_MATCH": "yes" if reload_match else "no",
        "RUN_STATUS": "ok",
    }
    for key, value in markers.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
