# PyTorch training engineering lab

This lab starts after a model can train once. It uses a tiny PyTorch classifier to show what a training run must leave behind when someone else needs to debug, resume, compare or publish it.

The synthetic task is intentionally simple: classify a point `(x, y)` as class `1` when `x + y > 0`, otherwise class `0`. Because the task is linearly separable, model quality is not the hard part. The hard part is the engineering contract around the run:

- a config file and stable config hash;
- explicit train/validation/test splits;
- simple baselines before the model result;
- `model.train()` for updates and `model.eval()` plus `torch.no_grad()` for evaluation;
- checkpoints containing model, optimizer, scheduler, epoch and config hash;
- exact resume from a mid-run checkpoint;
- JSONL event logs, a model card and an artifact manifest.

## Prerequisite

This lab requires PyTorch. If your default `python3` does not have `torch`, create or select a Python environment with PyTorch installed, then pass it through `PYTORCH_LAB_PYTHON`:

```bash
PYTORCH_LAB_PYTHON=/path/to/python ./run_lab.sh
```

The lab runs on CPU by default for deterministic evidence.

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
CONFIG_HASH_MATCH=yes
TRAIN_SAMPLES=60
VAL_SAMPLES=16
TEST_SAMPLES=14
MAJORITY_BASELINE_ACC=0.500
HEURISTIC_BASELINE_ACC=0.786
FINAL_VAL_ACC=1.000
FINAL_TEST_ACC=1.000
BEST_CHECKPOINT_RELOAD_MATCH=yes
RESUME_MATCHES_FULL_RUN=yes
JSONL_LOG_ROWS=12
MODEL_CARD_READY=yes
ARTIFACT_MANIFEST_READY=yes
RUN_STATUS=ok
deep_learning_pytorch_training_engineering_lab_status=ok
```

The generated `reports/` directory is local evidence. Public copies should contain the source, tests and runner only, not generated reports, checkpoints, Python caches or local wrapper scripts.

## What the reports mean

- `training_engineering_probe.json`: machine-readable summary of baselines, metrics and gates.
- `full_events.jsonl`: one event per uninterrupted training epoch.
- `resume_events.jsonl`: events from the resumed part of the run.
- `test_predictions.csv`: logits and predictions for the test split.
- `model_card.md`: short task, split, metric and limitation note.
- `artifact_manifest.json`: SHA-256 manifest for generated local evidence.
- `checkpoints/*.pt`: local checkpoints generated during the run; do not publish them as source assets.

## Boundary

This lab proves the training wrapper on a tiny deterministic CPU task. It does not claim production model quality, natural-data generalization, mixed precision safety, distributed checkpointing, or GPU performance.
