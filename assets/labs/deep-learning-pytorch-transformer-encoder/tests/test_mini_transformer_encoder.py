#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import torch

from mini_transformer_encoder import (
    MAX_LEN,
    TinyTransformerEncoderClassifier,
    accuracy,
    build_probe,
    make_train_test,
    majority_predictor,
    predict_bag_sorted,
    predict_last_token,
    samples_to_tensors,
)


class MiniTransformerEncoderTests(unittest.TestCase):
    def test_dataset_and_baselines_are_order_sensitive(self) -> None:
        train, test = make_train_test()
        self.assertEqual(len(train), 48)
        self.assertEqual(len(test), 8)
        self.assertEqual(accuracy(test, majority_predictor(train)), 0.25)
        self.assertEqual(accuracy(test, predict_last_token), 0.5)
        self.assertEqual(accuracy(test, predict_bag_sorted), 0.75)

    def test_padding_mask_shape(self) -> None:
        _train, test = make_train_test()
        input_ids, labels, padding_mask = samples_to_tensors(test)
        self.assertEqual(tuple(input_ids.shape), (8, MAX_LEN))
        self.assertEqual(tuple(labels.shape), (8,))
        self.assertEqual(tuple(padding_mask.shape), (8, MAX_LEN))
        self.assertEqual(int(padding_mask.sum().item()), 8)
        self.assertEqual(padding_mask.dtype, torch.bool)

    def test_model_forward_shape(self) -> None:
        _train, test = make_train_test()
        input_ids, _labels, padding_mask = samples_to_tensors(test)
        torch.manual_seed(20260713)
        model = TinyTransformerEncoderClassifier()
        logits = model(input_ids, padding_mask)
        self.assertEqual(tuple(logits.shape), (8, 4))

    def test_probe_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            probe = build_probe(Path(tmp), device_name="cpu")
        self.assertEqual(probe["majority_baseline_accuracy"], 0.25)
        self.assertEqual(probe["last_token_baseline_accuracy"], 0.5)
        self.assertEqual(probe["bag_sorted_baseline_accuracy"], 0.75)
        self.assertEqual(probe["transformer_train_accuracy"], 1.0)
        self.assertEqual(probe["transformer_test_accuracy"], 1.0)
        self.assertEqual(probe["transformer_gain_over_best_baseline"], 0.25)
        self.assertEqual(probe["loss_decreased"], True)
        self.assertEqual(probe["padding_mask_shape_ok"], True)
        self.assertEqual(probe["padding_mask_true_count"], 8)
        self.assertEqual(probe["position_embedding_present"], True)
        self.assertEqual(probe["checkpoint_reload_match"], True)
        self.assertEqual(probe["run_status"], "ok")


if __name__ == "__main__":
    unittest.main()
