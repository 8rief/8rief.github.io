#!/usr/bin/env python3
from __future__ import annotations

import unittest

from attention_lookup import (
    KEYS,
    VALUES,
    accuracy,
    attention_trace,
    build_probe,
    make_dataset,
    predict_attention,
    predict_fixed_summary,
    predict_last_value,
    scaled_dot_product_attention,
    key_vector,
    value_vector,
)


class AttentionLookupTests(unittest.TestCase):
    def test_dataset_is_balanced_key_value_lookup_task(self) -> None:
        train, test = make_dataset()
        self.assertEqual(len(train), 32)
        self.assertEqual(len(test), 32)
        self.assertEqual({len(sample.slots) for sample in train + test}, {4})
        for sample in train + test:
            self.assertEqual(tuple(slot.key for slot in sample.slots), KEYS)
            self.assertEqual(sorted(slot.value for slot in sample.slots), sorted(VALUES))
            self.assertIn(sample.query, KEYS)
            self.assertEqual({slot.key: slot.value for slot in sample.slots}[sample.query], sample.label)
        test_label_counts = {value: sum(1 for sample in test if sample.label == value) for value in VALUES}
        self.assertEqual(set(test_label_counts.values()), {8})

    def test_scaled_dot_product_attention_selects_matching_key(self) -> None:
        query = key_vector("blue")
        keys = [key_vector(key) for key in KEYS]
        values = [value_vector(value) for value in VALUES]
        output, weights, scores = scaled_dot_product_attention(query, keys, values)
        self.assertGreater(weights[KEYS.index("blue")], 0.70)
        self.assertEqual(max(range(len(weights)), key=weights.__getitem__), KEYS.index("blue"))
        self.assertEqual(max(range(len(output)), key=output.__getitem__), VALUES.index("sky"))
        self.assertGreater(scores[KEYS.index("blue")], scores[KEYS.index("red")])

    def test_baselines_cannot_use_key_value_binding(self) -> None:
        _train, test = make_dataset()
        self.assertEqual(accuracy(test, predict_last_value), 0.25)
        self.assertEqual(accuracy(test, predict_fixed_summary), 0.25)

    def test_attention_solves_all_test_samples(self) -> None:
        _train, test = make_dataset()
        self.assertEqual(accuracy(test, predict_attention), 1.0)
        for sample in test:
            trace = attention_trace(sample)
            self.assertEqual(trace["prediction"], sample.label)
            self.assertEqual(trace["top_key"], sample.query)
            self.assertGreater(float(trace["top_weight"]), 0.70)

    def test_probe_contract(self) -> None:
        probe = build_probe()
        self.assertEqual(probe["majority_baseline_accuracy"], 0.25)
        self.assertEqual(probe["last_value_accuracy"], 0.25)
        self.assertEqual(probe["bag_of_values_accuracy"], 0.25)
        self.assertEqual(probe["fixed_summary_accuracy"], 0.25)
        self.assertEqual(probe["attention_lookup_accuracy"], 1.0)
        self.assertEqual(probe["attention_gain_over_best_baseline"], 0.75)
        self.assertEqual(probe["all_top_keys_match_query"], True)
        self.assertEqual(probe["run_status"], "ok")


if __name__ == "__main__":
    unittest.main()
