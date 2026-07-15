# PyTorch character language-model lab

This lab trains a tiny character-level GRU language model on a synthetic grammar. The first character is a long-range cue: after a shared middle string and delimiter, the model must predict `A`, `B` or `C`. A bigram baseline sees only the delimiter before that final label, so it cannot solve the dependency.

The pipeline is:

```text
raw string -> character vocabulary -> shifted input/target pairs -> DataLoader + collate_fn -> Embedding -> GRU hidden states -> Linear logits -> CrossEntropyLoss(ignore_index=-100)
```

## Prerequisite

This lab requires PyTorch. If your default `python3` cannot import `torch`, pass an interpreter explicitly:

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
TRAIN_SAMPLES=18
VAL_SAMPLES=9
TEST_SAMPLES=9
UNIGRAM_FINAL_ACC=0.000
BIGRAM_FINAL_ACC=0.333
MODEL_VAL_FINAL_ACC=1.000
MODEL_FINAL_ACC=1.000
MODEL_BEATS_BIGRAM_FINAL=yes
PROMPT_A_NEXT=A
PROMPT_B_NEXT=B
PROMPT_C_NEXT=C
TEACHER_FORCING_SHIFT_OK=yes
CHECKPOINT_RELOAD_MATCH=yes
RUN_STATUS=ok
deep_learning_pytorch_char_lm_lab_status=ok
```

## What the reports mean

- `char_lm_probe.json`: split sizes, baselines, model metrics, prompt predictions and gates.
- `training_history.csv`: selected epoch metrics.
- `final_predictions.csv`: final-label predictions and top-3 probabilities on test examples.
- `vocab.json`: generated character vocabulary.
- `char_lm_report.md`: short human-readable summary.
- `checkpoint.pt`: local checkpoint generated during the run; do not publish it as a source asset.

## Boundary

The corpus is a tiny synthetic grammar. Perfect final-label accuracy proves that the pipeline can train a GRU to carry a cue across a short sequence. It does not prove open-domain text generation quality, robustness to real corpora, or good sampling behavior.
