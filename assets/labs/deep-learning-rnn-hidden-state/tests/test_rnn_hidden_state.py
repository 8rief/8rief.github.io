from __future__ import annotations

import unittest

from rnn_hidden_state import (
    LABEL_A,
    LABEL_B,
    build_probe,
    hidden_sign_stable,
    make_dataset,
    predict_no_recurrence,
    predict_recurrent,
    recurrent_step,
    suffix_bag_key,
    trace_sequence,
)


class RecurrentPrimitiveTests(unittest.TestCase):
    def test_first_cue_sets_hidden_sign(self) -> None:
        self.assertGreater(recurrent_step(0.0, "A"), 0.9)
        self.assertLess(recurrent_step(0.0, "B"), -0.9)

    def test_neutral_tokens_keep_recurrent_sign(self) -> None:
        positive_trace = trace_sequence(tuple("Axyyxx"))
        negative_trace = trace_sequence(tuple("Byxyxx"))
        self.assertTrue(all(value > 0.0 for value in positive_trace))
        self.assertTrue(all(value < 0.0 for value in negative_trace))

    def test_no_recurrence_forgets_before_final_neutral_token(self) -> None:
        self.assertEqual(predict_no_recurrence(tuple("Axyyxx")), LABEL_A)
        self.assertEqual(predict_no_recurrence(tuple("Byxyxx")), LABEL_A)
        self.assertEqual(predict_recurrent(tuple("Axyyxx")), LABEL_A)
        self.assertEqual(predict_recurrent(tuple("Byxyxx")), LABEL_B)


class DatasetAndProbeTests(unittest.TestCase):
    def test_dataset_balances_labels_and_suffixes(self) -> None:
        train, test = make_dataset()
        self.assertEqual(len(train), 8)
        self.assertEqual(len(test), 8)
        self.assertEqual(sum(1 for sample in train if sample.label == LABEL_A), 4)
        self.assertEqual(sum(1 for sample in train if sample.label == LABEL_B), 4)
        self.assertEqual({suffix_bag_key(sample.sequence) for sample in train}, {(("x", 3), ("y", 2))})
        self.assertEqual({suffix_bag_key(sample.sequence) for sample in test}, {(("x", 3), ("y", 2))})

    def test_hidden_sign_stability_for_all_samples(self) -> None:
        train, test = make_dataset()
        self.assertTrue(hidden_sign_stable(train + test))

    def test_probe_shows_memory_gain_over_forgetful_baselines(self) -> None:
        probe = build_probe()
        self.assertEqual(probe["run_status"], "ok")
        self.assertEqual(probe["majority_baseline_accuracy"], 0.5)
        self.assertEqual(probe["last_token_accuracy"], 0.5)
        self.assertEqual(probe["suffix_bag_accuracy"], 0.5)
        self.assertEqual(probe["no_recurrence_accuracy"], 0.5)
        self.assertEqual(probe["rnn_memory_accuracy"], 1.0)
        self.assertEqual(probe["memory_gain_over_best_baseline"], 0.5)


if __name__ == "__main__":
    unittest.main()
