from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from .data import make_xor_gaussians
from .train import (
    autograd_demo,
    compare_metrics,
    load_checkpoint_accuracy,
    majority_baseline,
    tensor_demo,
    train_model,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deep learning foundations teaching lab")
    sub = parser.add_subparsers(dest="command", required=True)

    env_p = sub.add_parser("env", help="print environment versions")
    env_p.add_argument("--output", type=Path)

    data_p = sub.add_parser("data-summary", help="write deterministic dataset summary")
    data_p.add_argument("--output", type=Path, required=True)

    tensor_p = sub.add_parser("demo-tensors", help="write tensor shape/broadcasting demo")
    tensor_p.add_argument("--output", type=Path, required=True)

    grad_p = sub.add_parser("demo-autograd", help="write autograd gradient-check demo")
    grad_p.add_argument("--output", type=Path, required=True)

    majority_p = sub.add_parser("majority", help="evaluate majority-class baseline")
    majority_p.add_argument("--output-dir", type=Path, required=True)

    train_p = sub.add_parser("train", help="train linear or MLP classifier")
    train_p.add_argument("--model", choices=["linear", "mlp"], required=True)
    train_p.add_argument("--output-dir", type=Path, required=True)
    train_p.add_argument("--epochs", type=int, default=200)
    train_p.add_argument("--learning-rate", type=float, default=0.03)

    check_p = sub.add_parser("checkpoint-check", help="load checkpoint and report accuracy")
    check_p.add_argument("--checkpoint", type=Path, required=True)
    check_p.add_argument("--output", type=Path, required=True)

    cmp_p = sub.add_parser("compare", help="compare baseline and MLP metrics")
    cmp_p.add_argument("--majority", type=Path, required=True)
    cmp_p.add_argument("--linear", type=Path, required=True)
    cmp_p.add_argument("--mlp", type=Path, required=True)
    cmp_p.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "env":
        data = {
            "python": ".".join(map(str, __import__("sys").version_info[:3])),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "torch_cuda_available": bool(torch.cuda.is_available()),
            "lab_device": "cpu",
        }
        if args.output:
            write_json(args.output, data)
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    elif args.command == "data-summary":
        bundle = make_xor_gaussians()
        write_json(args.output, bundle.summary())
        print(json.dumps(bundle.summary(), ensure_ascii=False, sort_keys=True))
    elif args.command == "demo-tensors":
        data = tensor_demo()
        write_json(args.output, data)
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    elif args.command == "demo-autograd":
        data = autograd_demo()
        write_json(args.output, data)
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    elif args.command == "majority":
        metrics = majority_baseline(make_xor_gaussians(), args.output_dir)
        print(json.dumps(metrics.__dict__, ensure_ascii=False, sort_keys=True))
    elif args.command == "train":
        result = train_model(
            args.model,
            args.output_dir,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
        )
        print(json.dumps({"model": result.model, "test_accuracy": result.test.accuracy, "test_loss": result.test.loss}, ensure_ascii=False, sort_keys=True))
    elif args.command == "checkpoint-check":
        acc = load_checkpoint_accuracy(args.checkpoint)
        data = {"checkpoint": str(args.checkpoint), "test_accuracy_after_load": acc}
        write_json(args.output, data)
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    elif args.command == "compare":
        data = compare_metrics(args.linear, args.mlp, args.majority, args.output)
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    else:
        raise AssertionError(args.command)


if __name__ == "__main__":
    main()
