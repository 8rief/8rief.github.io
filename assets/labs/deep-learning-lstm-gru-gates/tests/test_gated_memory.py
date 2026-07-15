#!/usr/bin/env python3
from __future__ import annotations

import unittest

from gated_memory import (
    LABEL_A,
    LABEL_B,
    accuracy,
    build_probe,
    gru_keep_stable,
    gru_trace,
    lstm_cell_state_stable,
    lstm_trace,
    make_dataset,
    predict_gru_gate,
    predict_lstm_gate,
    predict_vanilla_rnn,
)


class GatedMemoryTests(unittest.TestCase):
    def test_dataset_is_balanced_and_delayed_cue(self) -> None:
        train, test = make_dataset()
        self.assertEqual(len(train), 16)
        self.assertEqual(len(test), 16)
        self.assertEqual({len(sample.sequence) for sample in train + test}, {13})
        self.assertEqual(sum(1 for sample in test if sample.label == LABEL_A), 8)
        self.assertEqual(sum(1 for sample in test if sample.label == LABEL_B), 8)
        for left, right in zip(test[0::2], test[1::2]):
            self.assertNotEqual(left.sequence[0], right.sequence[0])
            self.assertEqual(left.sequence[1:], right.sequence[1:])
            self.assertNotEqual(left.label, right.label)

    def test_vanilla_rnn_is_overwritten_by_suffix_distractors(self) -> None:
        _train, test = make_dataset()
        self.assertEqual(accuracy(test, predict_vanilla_rnn), 0.5)

    def test_lstm_gates_write_once_then_keep_cell_state(self) -> None:
        train, test = make_dataset()
        self.assertTrue(lstm_cell_state_stable(train + test))
        self.assertEqual(accuracy(test, predict_lstm_gate), 1.0)
        trace = lstm_trace(("A", "y", "y", "x"))
        self.assertEqual([step.input_gate for step in trace], [1.0, 0.0, 0.0, 0.0])
        self.assertEqual([step.forget_gate for step in trace], [0.0, 1.0, 1.0, 1.0])
        self.assertEqual([step.cell for step in trace], [1.0, 1.0, 1.0, 1.0])

    def test_gru_update_gate_writes_once_then_keeps_hidden_state(self) -> None:
        train, test = make_dataset()
        self.assertTrue(gru_keep_stable(train + test))
        self.assertEqual(accuracy(test, predict_gru_gate), 1.0)
        trace = gru_trace(("B", "x", "x", "y"))
        self.assertEqual([step.update_gate for step in trace], [0.0, 1.0, 1.0, 1.0])
        self.assertLess(trace[0].hidden, 0.0)
        self.assertEqual(trace[-1].hidden, trace[0].hidden)

    def test_probe_contract(self) -> None:
        probe = build_probe()
        self.assertEqual(probe["majority_baseline_accuracy"], 0.5)
        self.assertEqual(probe["last_token_accuracy"], 0.5)
        self.assertEqual(probe["vanilla_rnn_accuracy"], 0.5)
        self.assertEqual(probe["lstm_gate_accuracy"], 1.0)
        self.assertEqual(probe["gru_update_gate_accuracy"], 1.0)
        self.assertEqual(probe["gate_gain_over_best_baseline"], 0.5)
        self.assertEqual(probe["run_status"], "ok")


if __name__ == "__main__":
    unittest.main()
