# Deep learning LSTM/GRU gate memory lab

This lab explains why sequence models add gates after the basic recurrent hidden state. It uses pure Python and a synthetic delayed-cue task so the result is visible without NumPy, PyTorch or a GPU.

## Run

```bash
./run_lab.sh
```

Expected stable markers:

```text
TRAIN_SAMPLES=16
TEST_SAMPLES=16
SEQUENCE_LENGTH=13
MAJORITY_BASELINE_ACC=0.500
LAST_TOKEN_ACC=0.500
VANILLA_RNN_ACC=0.500
LSTM_GATE_ACC=1.000
GRU_UPDATE_GATE_ACC=1.000
GATE_GAIN_OVER_BEST_BASELINE=0.500
LSTM_CELL_STABLE=yes
GRU_KEEP_STABLE=yes
RUN_STATUS=ok
deep_learning_lstm_gru_lab_status=ok
```

## What the experiment does

Each sequence has one cue token followed by twelve distractor tokens. The first token `A` or `B` determines the label. The later `x/y` suffix is paired with both labels, so a majority rule, a last-token rule and a suffix-overwritten vanilla RNN stay at chance on the test set.

The lab then compares two idealized gated cells:

- LSTM-style gate memory writes the first cue into a cell state, then sets the input gate to zero and the forget gate to one for distractors.
- GRU-style update gate memory writes the first cue, then sets the update gate to one for distractors so the hidden state is kept.

Generated reports live under `reports/` after you run the lab:

- `gate_probe.json`: machine-readable metrics and traces.
- `gate_report.md`: method comparison and interpretation.
- `trace_table.csv`: per-sample predictions and final states.

`reports/` is generated evidence and is not committed to the public package.

## Boundary

The gates in this lab are hand-set to make the mechanism inspectable. A real LSTM or GRU learns gate weights from data and uses continuous sigmoid/tanh values. This lab proves one mechanism: a gate can separate write, keep and expose decisions so later distractors do not overwrite the earlier cue. It is not a language-model benchmark.
