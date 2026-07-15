from __future__ import annotations

import unittest

import torch
from torch import nn

from char_lm import (
    BOS,
    EOS,
    PAD,
    bigram_baseline,
    build_vocab,
    encode_example,
    evaluate_model,
    make_loader,
    split_examples,
    train_model,
)


class CharLanguageModelTests(unittest.TestCase):
    def test_vocab_and_shift(self) -> None:
        splits = split_examples()
        vocab = build_vocab(splits["train"])
        self.assertEqual(vocab[PAD], 0)
        self.assertEqual(vocab[BOS], 1)
        self.assertEqual(vocab[EOS], 2)
        input_ids, target_ids, label_position = encode_example(splits["train"][0], vocab)
        self.assertEqual(input_ids[0].item(), vocab[BOS])
        self.assertEqual(target_ids[-1].item(), vocab[EOS])
        self.assertEqual(target_ids[label_position].item(), vocab[splits["train"][0].label])

    def test_bigram_final_boundary(self) -> None:
        splits = split_examples()
        bigram = bigram_baseline(splits["train"], splits["test"])
        self.assertAlmostEqual(float(bigram["final_accuracy"]), 1 / 3, places=3)
        self.assertEqual(bigram["delimiter_prediction"], "A")

    def test_model_learns_final_dependency(self) -> None:
        splits = split_examples()
        vocab = build_vocab(splits["train"])
        model, _ = train_model(splits["train"], splits["val"], vocab, epochs=80)
        loader = make_loader(splits["test"], vocab, batch_size=9, shuffle=False, seed=20260714)
        metrics = evaluate_model(model, loader, nn.CrossEntropyLoss(ignore_index=-100), vocab)
        self.assertGreaterEqual(float(metrics["final_accuracy"]), 0.999)
        # The held-out middle strings intentionally make full-token accuracy
        # a weaker signal; the lab claim is the final long-range dependency.
        self.assertGreater(float(metrics["token_accuracy"]), 0.50)


if __name__ == "__main__":
    unittest.main()
