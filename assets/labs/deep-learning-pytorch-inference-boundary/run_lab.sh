#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTORCH_LAB_PYTHON:-python3}"

rm -rf reports .lab_tmp __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports .lab_tmp

echo "lab=deep-learning-pytorch-inference-boundary"
echo "pwd=$PWD"
echo "python_bin=$PYTHON_BIN"
echo "python_version=$($PYTHON_BIN --version)"

if ! "$PYTHON_BIN" - <<'PY' >/tmp/pytorch-inference-boundary-import-check.txt 2>&1
import torch
print(torch.__version__)
PY
then
  cat /tmp/pytorch-inference-boundary-import-check.txt >&2 || true
  echo "ERROR: selected Python cannot import torch. Install PyTorch or set PYTORCH_LAB_PYTHON=/path/to/python." >&2
  exit 2
fi
printf 'torch_version=%s\n' "$(cat /tmp/pytorch-inference-boundary-import-check.txt)"
rm -f /tmp/pytorch-inference-boundary-import-check.txt

echo
echo "syntax check"
"$PYTHON_BIN" -m py_compile src/inference_boundary.py scripts/inference_probe.py

echo
echo "unit tests"
PYTHONPATH=src "$PYTHON_BIN" -m unittest discover -s tests -v

echo
echo "PyTorch inference-boundary probe"
PYTHONPATH=src "$PYTHON_BIN" scripts/inference_probe.py | tee .lab_tmp/run_lab_output.txt
cp .lab_tmp/run_lab_output.txt reports/run_lab_output.txt
rm -rf .lab_tmp

echo
echo "visible result markers"
test -s reports/inference_probe.json
test -s reports/inference_report.md
test -s reports/training_history.csv
test -s reports/predictions.csv
test -s reports/artifact_manifest.json
test -s reports/checkpoint.pt
grep -q '"run_status": "ok"' reports/inference_probe.json
grep -q 'TRAIN_SAMPLES=' reports/run_lab_output.txt
grep -q 'MAJORITY_BASELINE_ACC=' reports/run_lab_output.txt
grep -q 'MODEL_TEST_ACC=' reports/run_lab_output.txt
grep -q 'MODEL_BEATS_BASELINE=yes' reports/run_lab_output.txt
grep -q 'TRAIN_MODE_OUTPUT_CHANGED=yes' reports/run_lab_output.txt
grep -q 'EVAL_OUTPUT_STABLE=yes' reports/run_lab_output.txt
grep -q 'INFERENCE_MODE_ENABLED_INSIDE=yes' reports/run_lab_output.txt
grep -q 'INFERENCE_REQUIRES_GRAD=no' reports/run_lab_output.txt
grep -q 'BATCH_OUTPUT_MATCH=yes' reports/run_lab_output.txt
grep -q 'BATCH_TIMING_RECORDED=yes' reports/run_lab_output.txt
grep -q 'CHECKPOINT_RELOAD_MATCH=yes' reports/run_lab_output.txt
grep -q 'RUN_STATUS=ok' reports/run_lab_output.txt
printf 'probe_ready=reports/inference_probe.json\n'
printf 'report_ready=reports/inference_report.md\n'
printf 'history_ready=reports/training_history.csv\n'
printf 'predictions_ready=reports/predictions.csv\n'
printf 'manifest_ready=reports/artifact_manifest.json\n'
printf 'checkpoint_ready=reports/checkpoint.pt\n'
printf 'deep_learning_pytorch_inference_boundary_lab_status=ok\n'
