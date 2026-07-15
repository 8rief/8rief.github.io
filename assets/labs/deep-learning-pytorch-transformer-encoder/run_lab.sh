#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTORCH_LAB_PYTHON:-python3}"
DEVICE="${PYTORCH_LAB_DEVICE:-cpu}"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=deep-learning-pytorch-transformer-encoder"
echo "pwd=$PWD"
echo "python_bin=$PYTHON_BIN"
echo "python_version=$($PYTHON_BIN --version)"
echo "device=$DEVICE"

if ! "$PYTHON_BIN" - <<'PY' >/tmp/pytorch-transformer-import-check.txt 2>&1
import torch
print(torch.__version__)
PY
then
  cat /tmp/pytorch-transformer-import-check.txt >&2 || true
  echo "ERROR: selected Python cannot import torch. Install PyTorch or set PYTORCH_LAB_PYTHON=/path/to/python." >&2
  exit 2
fi
printf 'torch_version=%s\n' "$(cat /tmp/pytorch-transformer-import-check.txt)"
rm -f /tmp/pytorch-transformer-import-check.txt

echo
echo "syntax check"
"$PYTHON_BIN" -m py_compile src/mini_transformer_encoder.py scripts/pytorch_transformer_probe.py

echo
echo "unit tests"
PYTHONPATH=src "$PYTHON_BIN" -m unittest discover -s tests -v

echo
echo "PyTorch Transformer encoder project probe"
PYTHONPATH=src "$PYTHON_BIN" scripts/pytorch_transformer_probe.py --device "$DEVICE" | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/pytorch_transformer_probe.json
test -s reports/pytorch_transformer_report.md
test -s reports/training_history.csv
test -s reports/prediction_table.csv
test -s reports/checkpoint.pt
grep -q '"run_status": "ok"' reports/pytorch_transformer_probe.json
grep -q 'MAJORITY_BASELINE_ACC=0.250' reports/run_lab_output.txt
grep -q 'LAST_TOKEN_BASELINE_ACC=0.500' reports/run_lab_output.txt
grep -q 'BAG_SORTED_BASELINE_ACC=0.750' reports/run_lab_output.txt
grep -q 'TRANSFORMER_TEST_ACC=1.000' reports/run_lab_output.txt
grep -q 'TRANSFORMER_GAIN_OVER_BEST_BASELINE=0.250' reports/run_lab_output.txt
grep -q 'LOSS_DECREASED=yes' reports/run_lab_output.txt
grep -q 'PADDING_MASK_SHAPE_OK=yes' reports/run_lab_output.txt
grep -q 'PADDING_MASK_TRUE_COUNT=8' reports/run_lab_output.txt
grep -q 'POSITION_EMBEDDING_PRESENT=yes' reports/run_lab_output.txt
grep -q 'CHECKPOINT_RELOAD_MATCH=yes' reports/run_lab_output.txt
printf 'probe_ready=reports/pytorch_transformer_probe.json\n'
printf 'report_ready=reports/pytorch_transformer_report.md\n'
printf 'history_ready=reports/training_history.csv\n'
printf 'prediction_table_ready=reports/prediction_table.csv\n'
printf 'checkpoint_ready=reports/checkpoint.pt\n'
printf 'deep_learning_pytorch_transformer_encoder_lab_status=ok\n'
