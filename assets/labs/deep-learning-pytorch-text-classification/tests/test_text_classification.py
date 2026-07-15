from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import torch

from text_classification import (
    PAD,
    UNK,
    build_vocab,
    encode,
    first_token_baseline,
    keyword_rule_baseline,
    majority_baseline,
    make_loader,
    reload_checkpoint,
    split_examples,
    train_model,
    checkpoint_payload,
    evaluate,
)


class TextClassificationTests(unittest.TestCase):
    def test_vocab_and_encoding_have_special_tokens(self) -> None:
        splits = split_examples()
        vocab = build_vocab(splits["train"])
        self.assertEqual(vocab[PAD], 0)
        self.assertEqual(vocab[UNK], 1)
        encoded = encode("unknownword invoice", vocab)
        self.assertEqual(encoded[0], vocab[UNK])
        self.assertIn(vocab["invoice"], encoded)

    def test_collate_pads_variable_length_text(self) -> None:
        splits = split_examples()
        vocab = build_vocab(splits["train"])
        loader = make_loader(splits["test"], vocab, batch_size=9, shuffle=False, seed=1)
        batch = next(iter(loader))
        self.assertEqual(batch.input_ids.shape[0], 9)
        self.assertEqual(batch.labels.shape[0], 9)
        self.assertTrue((batch.lengths <= batch.input_ids.shape[1]).all().item())
        self.assertGreater(int(batch.input_ids.eq(vocab[PAD]).sum().item()), 0)

    def test_baselines_and_training_checkpoint(self) -> None:
        splits = split_examples()
        vocab = build_vocab(splits["train"])
        self.assertAlmostEqual(majority_baseline(splits["test"]), 1 / 3)
        self.assertAlmostEqual(first_token_baseline(splits["train"], splits["test"]), 1 / 3)
        self.assertEqual(keyword_rule_baseline(splits["test"]), 1.0)
        model, history = train_model(splits["train"], splits["val"], vocab, epochs=18)
        loss_fn = torch.nn.CrossEntropyLoss()
        loader = make_loader(splits["test"], vocab, batch_size=9, shuffle=False, seed=1)
        metrics = evaluate(model, loader, loss_fn)
        self.assertEqual(metrics["accuracy"], 1.0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.pt"
            torch.save(checkpoint_payload(model, vocab, history, metrics), path)
            reloaded, _vocab, _checkpoint = reload_checkpoint(path)
            reloaded_metrics = evaluate(reloaded, loader, loss_fn)
            self.assertEqual(reloaded_metrics["predictions"], metrics["predictions"])


if __name__ == "__main__":
    unittest.main()
