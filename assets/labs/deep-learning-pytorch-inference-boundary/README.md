# PyTorch inference-boundary lab

This lab trains a tiny 2D classifier and then switches to inference. The model contains Dropout and BatchNorm so that `model.eval()` has a visible effect. The lab checks `eval()`, `torch.inference_mode()`, checkpoint reload, batch-vs-single output equality, prediction-table output and a small local timing smoke test.

The pipeline is:

```text
train toy classifier -> save checkpoint -> load model -> model.eval() -> torch.inference_mode() -> batch predictions -> local timing/report
```

## Prerequisite

This lab requires PyTorch. If your default `python3` cannot import `torch`, pass an interpreter explicitly:

```bash
PYTORCH_LAB_PYTHON=/path/to/python ./run_lab.sh
```

The lab runs on CPU and uses deterministic settings. Timing values are local smoke evidence, not production benchmarks.

## Run

```bash
./run_lab.sh
```

Expected stable markers include:

```text
MODEL_BEATS_BASELINE=yes
TRAIN_MODE_OUTPUT_CHANGED=yes
EVAL_OUTPUT_STABLE=yes
INFERENCE_MODE_ENABLED_INSIDE=yes
INFERENCE_REQUIRES_GRAD=no
BATCH_OUTPUT_MATCH=yes
BATCH_TIMING_RECORDED=yes
CHECKPOINT_RELOAD_MATCH=yes
RUN_STATUS=ok
deep_learning_pytorch_inference_boundary_lab_status=ok
```

## What the reports mean

- `inference_probe.json`: split sizes, metrics, mode checks, single-vs-batch check, timing and checkpoint hash.
- `training_history.csv`: selected training epochs.
- `predictions.csv`: test predictions with sample id, features, gold label, predicted label and probability.
- `artifact_manifest.json`: generated report/checkpoint manifest.
- `inference_report.md`: short human-readable summary.
- `checkpoint.pt`: local checkpoint generated during the run; do not publish it as a source asset.

## Boundary

This lab proves the inference-mode mechanics on a tiny CPU toy model. It does not benchmark production latency, GPU throughput, quantization, model serving, ONNX export, or distributed inference. Those require separate measurement boundaries.
