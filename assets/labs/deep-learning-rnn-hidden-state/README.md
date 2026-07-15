# Deep learning RNN hidden-state foundations lab

This lab explains the first recurrent-neural-network idea without depending on NumPy or PyTorch. It uses pure Python to show how a hidden state can carry an early sequence cue to the final prediction.

## Run

```bash
./run_lab.sh
```

Expected stable markers:

```text
TRAIN_SAMPLES=8
TEST_SAMPLES=8
SEQUENCE_LENGTH=6
MAJORITY_BASELINE_ACC=0.500
LAST_TOKEN_ACC=0.500
SUFFIX_BAG_ACC=0.500
NO_RECURRENCE_ACC=0.500
RNN_MEMORY_ACC=1.000
MEMORY_GAIN_OVER_BEST_BASELINE=0.500
HIDDEN_SIGN_STABLE=yes
RUN_STATUS=ok
deep_learning_rnn_lab_status=ok
```

## What the experiment does

Each sequence has six tokens. The first token is `A` or `B` and determines the label. The remaining suffix tokens are neutral `x`/`y` tokens with balanced counts and endings, so majority, last-token, suffix-bag, and no-recurrence baselines cannot solve the held-out test set.

The recurrent update uses the same rule at every step:

```text
h_t = tanh(2.0 * h_{t-1} + 3.0 * input_t)
```

`A` maps to `+1`, `B` maps to `-1`, and neutral tokens map to `0`. After the first token sets the hidden-state sign, the recurrent term carries that sign through the neutral suffix.

Generated reports live under `reports/` after you run the lab:

- `rnn_probe.json`: machine-readable metrics and per-sample traces.
- `rnn_report.md`: human-readable comparison table.
- `trace_table.csv`: per-sample predictions and hidden-state values.

`reports/` is generated evidence and is not committed to the public package.

## Boundary

This is not a language-model benchmark. It proves one mechanism: a recurrent hidden state can carry early evidence to a later prediction. Real sequence models add learned weights, embeddings, losses, optimizers, gating, attention, much larger datasets, and harder evaluation.
