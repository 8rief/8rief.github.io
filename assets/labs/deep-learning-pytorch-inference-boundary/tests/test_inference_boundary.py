from __future__ import annotations

import unittest

from torch import nn

from inference_boundary import (
    check_mode_boundaries,
    compare_single_vs_batch,
    evaluate,
    make_examples,
    make_loader,
    majority_baseline_accuracy,
    train_model,
)


class InferenceBoundaryTests(unittest.TestCase):
    def test_model_beats_majority_baseline(self) -> None:
        splits = make_examples()
        model, _ = train_model(splits["train"], splits["val"], epochs=80)
        loader = make_loader(splits["test"], batch_size=128, shuffle=False, seed=20260714)
        metrics = evaluate(model, loader, nn.CrossEntropyLoss())
        baseline = majority_baseline_accuracy(splits["train"], splits["test"])
        self.assertGreater(float(metrics["accuracy"]), baseline)
        self.assertGreater(float(metrics["accuracy"]), 0.97)

    def test_eval_and_inference_boundaries(self) -> None:
        splits = make_examples()
        model, _ = train_model(splits["train"], splits["val"], epochs=40)
        checks = check_mode_boundaries(model, splits["test"][0])
        self.assertTrue(checks["train_mode_output_changed"])
        self.assertTrue(checks["eval_output_stable"])
        self.assertTrue(checks["inference_mode_enabled_inside"])
        self.assertFalse(checks["inference_requires_grad"])

    def test_batch_and_single_outputs_match_in_eval(self) -> None:
        splits = make_examples()
        model, _ = train_model(splits["train"], splits["val"], epochs=40)
        compare = compare_single_vs_batch(model, splits["test"][:16])
        self.assertTrue(compare["batch_output_match"])
        self.assertLess(compare["max_batch_single_diff"], 1e-5)


if __name__ == "__main__":
    unittest.main()
