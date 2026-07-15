from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from training_engineering import (
    build_splits,
    checkpoint_logits_match,
    config_hash,
    config_to_dict,
    majority_baseline_accuracy,
    read_config,
    reset_reports_dir,
    run_training,
    state_dicts_allclose,
    x_only_heuristic_accuracy,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "training_config.json"


class TrainingEngineeringTests(unittest.TestCase):
    def test_split_sizes_and_baselines_are_balanced(self) -> None:
        config = read_config(CONFIG_PATH)
        splits = build_splits(config)
        self.assertEqual(splits["train"].size, 60)
        self.assertEqual(splits["val"].size, 16)
        self.assertEqual(splits["test"].size, 14)
        self.assertEqual(majority_baseline_accuracy(splits["test"]), 0.5)
        self.assertAlmostEqual(x_only_heuristic_accuracy(splits["test"]), 0.785714, places=5)

    def test_config_hash_is_stable_and_changes_when_config_changes(self) -> None:
        config = read_config(CONFIG_PATH)
        original = config_hash(config)
        reloaded = type(config)(**config_to_dict(config))
        self.assertEqual(original, config_hash(reloaded))
        changed = type(config)(**{**config_to_dict(config), "learning_rate": 0.2})
        self.assertNotEqual(original, config_hash(changed))
        self.assertEqual(len(original), 64)

    def test_checkpoint_resume_matches_uninterrupted_run(self) -> None:
        config = read_config(CONFIG_PATH)
        splits = build_splits(config)
        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp) / "reports"
            reset_reports_dir(reports)
            full = run_training(config=config, splits=splits, reports_dir=reports, run_id="full")
            resumed = run_training(
                config=config,
                splits=splits,
                reports_dir=reports,
                run_id="resume",
                resume_checkpoint=Path(full["checkpoint_epoch_path"]),
            )
            self.assertTrue(state_dicts_allclose(Path(full["final_path"]), Path(resumed["final_path"])))
            self.assertTrue(checkpoint_logits_match(Path(full["best_path"]), config, splits["test"]))
            self.assertEqual(full["final_metrics"]["val"]["accuracy"], 1.0)
            self.assertEqual(full["final_metrics"]["test"]["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
