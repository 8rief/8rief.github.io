# PyTorch mini Transformer encoder project

This lab turns the previous pure-Python Transformer mechanisms into a small PyTorch project. It trains a tiny `nn.TransformerEncoder` classifier on an order-sensitive synthetic task and records baselines, training history, padding-mask checks and checkpoint reload evidence.

The task is deliberately small:

```text
input = <cls> token_0 token_1 N <pad>
label = ordered pair token_0 token_1, one of AA / AB / BA / BB
```

The bag of tokens cannot distinguish `AB` from `BA`, so the lab compares deterministic baselines against a position-aware Transformer encoder.

## Prerequisite

This lab requires PyTorch. If your default `python3` does not have `torch`, create or select a Python environment with PyTorch installed, then pass it through `PYTORCH_LAB_PYTHON`:

```bash
PYTORCH_LAB_PYTHON=/path/to/python ./run_lab.sh
```

The lab runs on CPU by default for deterministic evidence. CUDA may be available, but it is not required for this package.

## Run

```bash
./run_lab.sh
```

or explicitly:

```bash
PYTORCH_LAB_PYTHON=/path/to/python ./run_lab.sh
```

Expected stable markers:

```text
TRAIN_SAMPLES=48
TEST_SAMPLES=8
SEQUENCE_LENGTH=5
LABEL_COUNT=4
MAJORITY_BASELINE_ACC=0.250
LAST_TOKEN_BASELINE_ACC=0.500
BAG_SORTED_BASELINE_ACC=0.750
TRANSFORMER_TRAIN_ACC=1.000
TRANSFORMER_TEST_ACC=1.000
TRANSFORMER_GAIN_OVER_BEST_BASELINE=0.250
LOSS_DECREASED=yes
PADDING_MASK_SHAPE_OK=yes
PADDING_MASK_TRUE_COUNT=8
POSITION_EMBEDDING_PRESENT=yes
CHECKPOINT_RELOAD_MATCH=yes
RUN_STATUS=ok
deep_learning_pytorch_transformer_encoder_lab_status=ok
```

The generated `reports/` directory is local evidence. Public copies should contain the source, tests and runner only, not generated reports, checkpoints or Python caches.

## What the reports mean

- `pytorch_transformer_probe.json`: metrics, environment and gate results.
- `training_history.csv`: loss and accuracy at selected epochs.
- `prediction_table.csv`: per-sample logits and predictions.
- `pytorch_transformer_report.md`: concise human-readable summary.
- `checkpoint.pt`: local checkpoint generated during the run; do not publish it.

## Boundary

This lab proves that a tiny PyTorch Transformer encoder project is wired correctly on a synthetic order task. It does not prove broad language-model quality, large-scale generalization, or GPU performance.
