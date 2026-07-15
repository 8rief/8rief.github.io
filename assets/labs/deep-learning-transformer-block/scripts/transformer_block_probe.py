#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from transformer_block import write_probe_reports


def yn(value: object) -> str:
    return "yes" if bool(value) else "no"


def main() -> None:
    probe = write_probe_reports(Path("reports"))
    print(f"PAIR_TEST_SAMPLES={probe['pair_test_samples']}")
    print(f"BLOCK_TEST_SAMPLES={probe['block_test_samples']}")
    print(f"SINGLE_FIRST_HEAD_ACC={probe['single_first_head_accuracy']:.3f}")
    print(f"SINGLE_SECOND_HEAD_ACC={probe['single_second_head_accuracy']:.3f}")
    print(f"SINGLE_BLEND_HEAD_ACC={probe['single_blend_head_accuracy']:.3f}")
    print(f"MULTI_HEAD_PAIR_ACC={probe['multi_head_pair_accuracy']:.3f}")
    print(f"MULTI_HEAD_GAIN_OVER_BEST_BASELINE={probe['multi_head_gain_over_best_baseline']:.3f}")
    print(f"MULTI_HEAD_MIN_TOP_WEIGHT={probe['multi_head_min_top_weight']:.3f}")
    print(f"HEADS_FOCUS_DIFFERENT_KEYS={yn(probe['heads_focus_different_keys'])}")
    print(f"NO_ATTENTION_BLOCK_ACC={probe['no_attention_block_accuracy']:.3f}")
    print(f"NO_RESIDUAL_BLOCK_ACC={probe['no_residual_block_accuracy']:.3f}")
    print(f"ATTENTION_RESIDUAL_FFN_ACC={probe['attention_residual_ffn_accuracy']:.3f}")
    print(f"BLOCK_GAIN_OVER_BEST_BASELINE={probe['block_gain_over_best_baseline']:.3f}")
    print(f"LAYER_NORM_MEAN_OK={yn(probe['layer_norm_mean_ok'])}")
    print(f"LAYER_NORM_RMS_OK={yn(probe['layer_norm_rms_ok'])}")
    print(f"RUN_STATUS={probe['run_status']}")


if __name__ == "__main__":
    main()
