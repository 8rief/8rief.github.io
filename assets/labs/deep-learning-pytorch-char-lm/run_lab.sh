#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTORCH_LAB_PYTHON:-python3}"

rm -rf reports .lab_tmp __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports .lab_tmp

echo "lab=deep-learning-pytorch-char-lm"
echo "pwd=$PWD"
echo "python_bin=$PYTHON_BIN"
echo "python_version=$($PYTHON_BIN --version)"

if ! "$PYTHON_BIN" - <<'PY' >/tmp/pytorch-char-lm-import-check.txt 2>&1
import torch
print(torch.__version__)
PY
then
  cat /tmp/pytorch-char-lm-import-check.txt >&2 || true
  echo "ERROR: selected Python cannot import torch. Install PyTorch or set PYTORCH_LAB_PYTHON=/path/to/python." >&2
  exit 2
fi
printf 'torch_version=%s\n' "$(cat /tmp/pytorch-char-lm-import-check.txt)"
rm -f /tmp/pytorch-char-lm-import-check.txt

echo
echo "syntax check"
"$PYTHON_BIN" -m py_compile src/char_lm.py scripts/char_lm_probe.py

echo
echo "unit tests"
PYTHONPATH=src "$PYTHON_BIN" -m unittest discover -s tests -v

echo
echo "PyTorch character language-model probe"
PYTHONPATH=src "$PYTHON_BIN" scripts/char_lm_probe.py | tee .lab_tmp/run_lab_output.txt
cp .lab_tmp/run_lab_output.txt reports/run_lab_output.txt
rm -rf .lab_tmp

echo
echo "visible result markers"
test -s reports/char_lm_probe.json
test -s reports/char_lm_report.md
test -s reports/training_history.csv
test -s reports/final_predictions.csv
test -s reports/vocab.json
test -s reports/checkpoint.pt
grep -q '"run_status": "ok"' reports/char_lm_probe.json
grep -q 'TRAIN_SAMPLES=18' reports/run_lab_output.txt
grep -q 'VAL_SAMPLES=9' reports/run_lab_output.txt
grep -q 'TEST_SAMPLES=9' reports/run_lab_output.txt
grep -q 'UNIGRAM_FINAL_ACC=0.000' reports/run_lab_output.txt
grep -q 'BIGRAM_FINAL_ACC=0.333' reports/run_lab_output.txt
grep -q 'MODEL_VAL_FINAL_ACC=1.000' reports/run_lab_output.txt
grep -q 'MODEL_FINAL_ACC=1.000' reports/run_lab_output.txt
grep -q 'MODEL_BEATS_BIGRAM_FINAL=yes' reports/run_lab_output.txt
grep -q 'PROMPT_A_NEXT=A' reports/run_lab_output.txt
grep -q 'PROMPT_B_NEXT=B' reports/run_lab_output.txt
grep -q 'PROMPT_C_NEXT=C' reports/run_lab_output.txt
grep -q 'TEACHER_FORCING_SHIFT_OK=yes' reports/run_lab_output.txt
grep -q 'CHECKPOINT_RELOAD_MATCH=yes' reports/run_lab_output.txt
grep -q 'RUN_STATUS=ok' reports/run_lab_output.txt
printf 'probe_ready=reports/char_lm_probe.json\n'
printf 'report_ready=reports/char_lm_report.md\n'
printf 'history_ready=reports/training_history.csv\n'
printf 'predictions_ready=reports/final_predictions.csv\n'
printf 'checkpoint_ready=reports/checkpoint.pt\n'
printf 'deep_learning_pytorch_char_lm_lab_status=ok\n'
