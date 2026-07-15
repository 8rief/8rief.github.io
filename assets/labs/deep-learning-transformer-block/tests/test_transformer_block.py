#!/usr/bin/env python3
from __future__ import annotations

import unittest

from transformer_block import (
    accuracy,
    build_probe,
    make_blend_predictor,
    make_block_dataset,
    make_pair_dataset,
    multi_head_pair_trace,
    predict_multi_head_pair,
    predict_no_attention_block,
    predict_no_residual_block,
    predict_single_first_head,
    predict_single_second_head,
    predict_transformer_block,
    single_blend_score,
    transformer_block_trace,
)


class TransformerBlockTests(unittest.TestCase):
    def test_pair_dataset_requires_two_independent_reads(self) -> None:
        train, test = make_pair_dataset()
        self.assertEqual(len(test), 8)
        self.assertEqual({sample.label for sample in test}, {"A|X", "A|Y", "B|X", "B|Y"})
        self.assertEqual(accuracy(test, predict_single_first_head), 0.5)
        self.assertEqual(accuracy(test, predict_single_second_head), 0.5)
        self.assertEqual(accuracy(test, make_blend_predictor(train)), 0.75)

    def test_blended_single_head_has_collision(self) -> None:
        samples = {sample.label: sample for sample in make_pair_dataset()[1]}
        self.assertAlmostEqual(single_blend_score(samples["A|Y"]), single_blend_score(samples["B|X"]), places=9)
        self.assertNotEqual(samples["A|Y"].label, samples["B|X"].label)

    def test_multi_head_focuses_different_positions(self) -> None:
        _train, test = make_pair_dataset()
        self.assertEqual(accuracy(test, predict_multi_head_pair), 1.0)
        for sample in test:
            trace = multi_head_pair_trace(sample)
            self.assertEqual(trace["prediction"], sample.label)
            self.assertEqual(trace["color_top_position"], 0)
            self.assertEqual(trace["shape_top_position"], 2)
            self.assertGreater(float(trace["color_weights"][0]), 0.9)
            self.assertGreater(float(trace["shape_weights"][2]), 0.9)

    def test_block_needs_attention_and_residual(self) -> None:
        _train, test = make_block_dataset()
        self.assertEqual(accuracy(test, predict_no_attention_block), 0.5)
        self.assertEqual(accuracy(test, predict_no_residual_block), 0.5)
        self.assertEqual(accuracy(test, predict_transformer_block), 1.0)

    def test_layer_norm_keeps_balanced_signal_shape(self) -> None:
        _train, test = make_block_dataset()
        for sample in test:
            trace = transformer_block_trace(sample)
            self.assertEqual(trace["prediction"], sample.label)
            self.assertAlmostEqual(float(trace["norm_mean"]), 0.0, places=9)
            self.assertAlmostEqual(float(trace["norm_rms"]), 1.0, places=9)

    def test_probe_contract(self) -> None:
        probe = build_probe()
        self.assertEqual(probe["single_first_head_accuracy"], 0.5)
        self.assertEqual(probe["single_second_head_accuracy"], 0.5)
        self.assertEqual(probe["single_blend_head_accuracy"], 0.75)
        self.assertEqual(probe["multi_head_pair_accuracy"], 1.0)
        self.assertEqual(probe["multi_head_gain_over_best_baseline"], 0.25)
        self.assertEqual(probe["heads_focus_different_keys"], True)
        self.assertEqual(probe["no_attention_block_accuracy"], 0.5)
        self.assertEqual(probe["no_residual_block_accuracy"], 0.5)
        self.assertEqual(probe["attention_residual_ffn_accuracy"], 1.0)
        self.assertEqual(probe["block_gain_over_best_baseline"], 0.5)
        self.assertEqual(probe["layer_norm_mean_ok"], True)
        self.assertEqual(probe["layer_norm_rms_ok"], True)
        self.assertEqual(probe["run_status"], "ok")


if __name__ == "__main__":
    unittest.main()
