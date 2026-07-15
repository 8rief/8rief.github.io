#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import train  # noqa: E402


class DeepLearningLabTests(unittest.TestCase):
    def test_training_outputs_baseline_comparison_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metrics = train.run(root)
            self.assertEqual(metrics["rows"], {"train": 600, "val": 200, "test": 200})
            self.assertGreaterEqual(metrics["mlp"]["test"]["accuracy"], 0.85)
            self.assertGreater(metrics["comparison"]["mlp_minus_linear_test_acc"], 0.20)
            self.assertLess(metrics["gradient_check"]["max_relative_error"], 1e-6)
            self.assertTrue((root / "reports" / "metrics.json").exists())
            self.assertTrue((root / "reports" / "training_curve.svg").exists())
            self.assertTrue((root / "models" / "mlp-weights.npz").exists())
            self.assertTrue((root / "models" / "model-card.md").exists())


if __name__ == "__main__":
    unittest.main()
