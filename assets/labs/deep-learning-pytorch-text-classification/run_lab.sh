#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTORCH_LAB_PYTHON:-python3}"

rm -rf reports .lab_tmp __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports .lab_tmp

echo "lab=deep-learning-pytorch-text-classification"
echo "pwd=$PWD"
echo "python_bin=$PYTHON_BIN"
echo "python_version=$($PYTHON_BIN --version)"

if ! "$PYTHON_BIN" - <<'PY' >/tmp/pytorch-text-classification-import-check.txt 2>&1
import torch
print(torch.__version__)
PY
then
  cat /tmp/pytorch-text-classification-import-check.txt >&2 || true
  echo "ERROR: selected Python cannot import torch. Install PyTorch or set PYTORCH_LAB_PYTHON=/path/to/python." >&2
  exit 2
fi
printf 'torch_version=%s\n' "$(cat /tmp/pytorch-text-classification-import-check.txt)"
rm -f /tmp/pytorch-text-classification-import-check.txt

echo
echo "syntax check"
"$PYTHON_BIN" -m py_compile src/text_classification.py scripts/text_classification_probe.py

echo
echo "unit tests"
PYTHONPATH=src "$PYTHON_BIN" -m unittest discover -s tests -v

echo
echo "PyTorch text classification probe"
PYTHONPATH=src "$PYTHON_BIN" scripts/text_classification_probe.py | tee .lab_tmp/run_lab_output.txt
cp .lab_tmp/run_lab_output.txt reports/run_lab_output.txt
rm -rf .lab_tmp

echo
echo "visible result markers"
test -s reports/text_classification_probe.json
test -s reports/text_classification_report.md
test -s reports/training_history.csv
test -s reports/confusion_matrix.csv
test -s reports/prediction_table.csv
test -s reports/vocab.json
test -s reports/checkpoint.pt
grep -q '"run_status": "ok"' reports/text_classification_probe.json
grep -q 'TRAIN_SAMPLES=36' reports/run_lab_output.txt
grep -q 'VAL_SAMPLES=9' reports/run_lab_output.txt
grep -q 'TEST_SAMPLES=9' reports/run_lab_output.txt
grep -q 'MAJORITY_BASELINE_ACC=0.333' reports/run_lab_output.txt
grep -q 'FIRST_TOKEN_BASELINE_ACC=0.333' reports/run_lab_output.txt
grep -q 'KEYWORD_RULE_BASELINE_ACC=1.000' reports/run_lab_output.txt
grep -q 'MODEL_VAL_ACC=1.000' reports/run_lab_output.txt
grep -q 'MODEL_TEST_ACC=1.000' reports/run_lab_output.txt
grep -q 'MODEL_MATCHES_KEYWORD_RULE=yes' reports/run_lab_output.txt
grep -q 'CONFUSION_DIAGONAL=3:3:3' reports/run_lab_output.txt
grep -q 'CHECKPOINT_RELOAD_MATCH=yes' reports/run_lab_output.txt
grep -q 'UNKNOWN_TOKEN_COUNT=4' reports/run_lab_output.txt
grep -q 'RUN_STATUS=ok' reports/run_lab_output.txt
printf 'probe_ready=reports/text_classification_probe.json\n'
printf 'report_ready=reports/text_classification_report.md\n'
printf 'history_ready=reports/training_history.csv\n'
printf 'confusion_ready=reports/confusion_matrix.csv\n'
printf 'predictions_ready=reports/prediction_table.csv\n'
printf 'checkpoint_ready=reports/checkpoint.pt\n'
printf 'deep_learning_pytorch_text_classification_lab_status=ok\n'
