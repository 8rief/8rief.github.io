#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from mini_transformer_encoder import build_probe


def yn(value: object) -> str:
    return "yes" if bool(value) else "no"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    probe = build_probe(Path("reports"), device_name=args.device)
    print(f"TORCH_VERSION={probe['torch_version']}")
    print(f"CUDA_AVAILABLE={yn(probe['cuda_available'])}")
    print(f"DEVICE={probe['device']}")
    print(f"TRAIN_SAMPLES={probe['train_samples']}")
    print(f"TEST_SAMPLES={probe['test_samples']}")
    print(f"SEQUENCE_LENGTH={probe['sequence_length']}")
    print(f"LABEL_COUNT={probe['label_count']}")
    print(f"MAJORITY_BASELINE_ACC={probe['majority_baseline_accuracy']:.3f}")
    print(f"LAST_TOKEN_BASELINE_ACC={probe['last_token_baseline_accuracy']:.3f}")
    print(f"BAG_SORTED_BASELINE_ACC={probe['bag_sorted_baseline_accuracy']:.3f}")
    print(f"TRANSFORMER_TRAIN_ACC={probe['transformer_train_accuracy']:.3f}")
    print(f"TRANSFORMER_TEST_ACC={probe['transformer_test_accuracy']:.3f}")
    print(f"TRANSFORMER_GAIN_OVER_BEST_BASELINE={probe['transformer_gain_over_best_baseline']:.3f}")
    print(f"LOSS_DECREASED={yn(probe['loss_decreased'])}")
    print(f"PADDING_MASK_SHAPE_OK={yn(probe['padding_mask_shape_ok'])}")
    print(f"PADDING_MASK_TRUE_COUNT={probe['padding_mask_true_count']}")
    print(f"POSITION_EMBEDDING_PRESENT={yn(probe['position_embedding_present'])}")
    print(f"CHECKPOINT_RELOAD_MATCH={yn(probe['checkpoint_reload_match'])}")
    print(f"RUN_STATUS={probe['run_status']}")


if __name__ == "__main__":
    main()
