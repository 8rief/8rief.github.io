from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from cnn_from_scratch import (
    HORIZONTAL_KERNEL,
    VERTICAL_KERNEL,
    add_bar,
    build_probe,
    conv2d,
    conv_features,
    make_dataset,
    max_pool2d,
    pad2d,
    relu,
)

ROOT = Path(__file__).resolve().parents[1]


class ConvolutionPrimitiveTests(unittest.TestCase):
    def test_padding_preserves_center_values(self) -> None:
        image = [[1.0, 2.0], [3.0, 4.0]]
        padded = pad2d(image, 1)
        self.assertEqual(len(padded), 4)
        self.assertEqual(len(padded[0]), 4)
        self.assertEqual(padded[1][1], 1.0)
        self.assertEqual(padded[2][2], 4.0)

    def test_conv2d_valid_shape_and_value(self) -> None:
        image = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
        kernel = [[1.0, 0.0], [0.0, -1.0]]
        out = conv2d(image, kernel)
        self.assertEqual(len(out), 2)
        self.assertEqual(len(out[0]), 2)
        self.assertEqual(out[0][0], -4.0)
        self.assertEqual(out[1][1], -4.0)

    def test_relu_and_pooling(self) -> None:
        feature = relu([[-1.0, 2.0], [3.0, -4.0]])
        self.assertEqual(feature, [[0.0, 2.0], [3.0, 0.0]])
        self.assertEqual(max_pool2d(feature, size=2, stride=2), [[3.0]])


class CnnMechanismTests(unittest.TestCase):
    def test_orientation_filters_respond_to_shifted_bars(self) -> None:
        vertical = conv_features(add_bar("vertical", 6))
        horizontal = conv_features(add_bar("horizontal", 6))
        self.assertGreater(vertical["vertical_response"], vertical["horizontal_response"])
        self.assertGreater(horizontal["horizontal_response"], horizontal["vertical_response"])

    def test_probe_shows_shift_generalization_over_raw_template(self) -> None:
        probe = build_probe()
        self.assertEqual(probe["run_status"], "ok")
        self.assertEqual(probe["conv_feature_accuracy"], 1.0)
        self.assertLess(probe["raw_template_accuracy"], probe["conv_feature_accuracy"])
        self.assertGreaterEqual(probe["shift_generalization_gain"], 0.5)

    def test_dataset_holds_out_positions(self) -> None:
        train, test = make_dataset()
        self.assertEqual({sample.position for sample in train}, {1, 2})
        self.assertEqual({sample.position for sample in test}, {5, 6})


if __name__ == "__main__":
    unittest.main()
