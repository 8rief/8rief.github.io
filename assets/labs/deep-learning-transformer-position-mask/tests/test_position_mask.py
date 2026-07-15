#!/usr/bin/env python3
from __future__ import annotations

import unittest

from position_mask import (
    accuracy,
    build_probe,
    future_lookup_trace,
    make_future_dataset,
    make_order_dataset,
    positional_attention_trace,
    predict_bag_order,
    predict_causal_masked_lookup,
    predict_no_position_attention,
    predict_positional_attention,
    predict_unmasked_future_lookup,
)


class PositionMaskTests(unittest.TestCase):
    def test_order_dataset_requires_position_information(self) -> None:
        _train, test = make_order_dataset()
        self.assertEqual(len(test), 8)
        self.assertEqual({sample.sequence for sample in test}, {("A", "B"), ("B", "A")})
        self.assertEqual({sample.label for sample in test}, {"A", "B"})
        self.assertEqual(accuracy(test, predict_bag_order), 0.5)
        self.assertEqual(accuracy(test, predict_no_position_attention), 0.5)

    def test_positional_attention_selects_query_position(self) -> None:
        _train, test = make_order_dataset()
        self.assertEqual(accuracy(test, predict_positional_attention), 1.0)
        for sample in test:
            trace = positional_attention_trace(sample)
            self.assertEqual(trace["prediction"], sample.label)
            self.assertEqual(trace["top_position"], sample.query_position)
            self.assertGreater(float(trace["top_weight"]), 0.80)

    def test_future_task_exposes_unmasked_leakage(self) -> None:
        _train, test = make_future_dataset()
        self.assertEqual(len(test), 8)
        self.assertEqual({sample.label for sample in test}, {"A", "B"})
        self.assertEqual(accuracy(test, predict_unmasked_future_lookup), 1.0)
        self.assertEqual(accuracy(test, predict_causal_masked_lookup), 0.5)

    def test_causal_mask_blocks_future_weight(self) -> None:
        _train, test = make_future_dataset()
        for sample in test:
            masked = future_lookup_trace(sample, causal=True)
            unmasked = future_lookup_trace(sample, causal=False)
            self.assertEqual(float(masked["future_weight"]), 0.0)
            self.assertGreater(float(unmasked["future_weight"]), 0.80)

    def test_probe_contract(self) -> None:
        probe = build_probe()
        self.assertEqual(probe["position_bag_baseline_accuracy"], 0.5)
        self.assertEqual(probe["no_position_attention_accuracy"], 0.5)
        self.assertEqual(probe["positional_attention_accuracy"], 1.0)
        self.assertEqual(probe["position_gain_over_best_baseline"], 0.5)
        self.assertEqual(probe["unmasked_future_lookup_accuracy"], 1.0)
        self.assertEqual(probe["causal_masked_lookup_accuracy"], 0.5)
        self.assertEqual(probe["mask_blocks_future"], True)
        self.assertEqual(probe["run_status"], "ok")


if __name__ == "__main__":
    unittest.main()
