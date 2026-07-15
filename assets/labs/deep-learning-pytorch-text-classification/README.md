# PyTorch text classification lab

This lab turns short support-ticket text into a small PyTorch classifier. The dataset is synthetic and keyword-driven on purpose: the goal is to understand the text pipeline, not to claim that a neural network beats a transparent rule.

The pipeline is:

```text
raw text -> tokenize -> vocabulary ids -> Dataset -> DataLoader + collate_fn -> padded batch -> mask-aware mean embedding -> logits -> CrossEntropyLoss
```

## Prerequisite

This lab requires PyTorch. If your default `python3` does not have `torch`, pass an interpreter explicitly:

```bash
PYTORCH_LAB_PYTHON=/path/to/python ./run_lab.sh
```

The lab runs on CPU and uses deterministic settings.

## Run

```bash
./run_lab.sh
```

Expected stable markers:

```text
TRAIN_SAMPLES=36
VAL_SAMPLES=9
TEST_SAMPLES=9
MAJORITY_BASELINE_ACC=0.333
FIRST_TOKEN_BASELINE_ACC=0.333
KEYWORD_RULE_BASELINE_ACC=1.000
MODEL_VAL_ACC=1.000
MODEL_TEST_ACC=1.000
MODEL_MATCHES_KEYWORD_RULE=yes
CONFUSION_DIAGONAL=3:3:3
CHECKPOINT_RELOAD_MATCH=yes
UNKNOWN_TOKEN_COUNT=4
RUN_STATUS=ok
deep_learning_pytorch_text_classification_lab_status=ok
```

The generated `reports/` directory is local evidence. Public copies should contain only the source, tests and runner, not generated reports, checkpoints, Python caches or local wrapper scripts.

## What the reports mean

- `text_classification_probe.json`: split sizes, baselines, model metrics and gates.
- `training_history.csv`: loss and accuracy per epoch.
- `confusion_matrix.csv`: gold-vs-predicted label counts on the test split.
- `prediction_table.csv`: text, gold label, predicted label and logits.
- `vocab.json`: generated vocabulary from the train split.
- `text_classification_report.md`: short human-readable summary.
- `checkpoint.pt`: local checkpoint generated during the run; do not publish it as a source asset.

## Boundary

A keyword rule already gets perfect accuracy on this toy dataset. That is the point: the lab teaches PyTorch text data plumbing and honest baseline reporting. It does not prove natural-language understanding, robustness to unseen wording, or production support-ticket quality.
