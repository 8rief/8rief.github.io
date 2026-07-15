#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTORCH_LAB_PYTHON:-python3}"
DEVICE="${PYTORCH_LAB_DEVICE:-cpu}"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__ .lab_tmp
mkdir -p reports

echo "lab=deep-learning-pytorch-training-engineering"
echo "pwd=$PWD"
echo "python_bin=$PYTHON_BIN"
echo "python_version=$($PYTHON_BIN --version)"
echo "device=$DEVICE"

if ! "$PYTHON_BIN" - <<'PY' >/tmp/pytorch-training-engineering-import-check.txt 2>&1
import torch
print(torch.__version__)
PY
then
  cat /tmp/pytorch-training-engineering-import-check.txt >&2 || true
  echo "ERROR: selected Python cannot import torch. Install PyTorch or set PYTORCH_LAB_PYTHON=/path/to/python." >&2
  exit 2
fi
printf 'torch_version=%s\n' "$(cat /tmp/pytorch-training-engineering-import-check.txt)"
rm -f /tmp/pytorch-training-engineering-import-check.txt

echo
echo "syntax check"
"$PYTHON_BIN" -m py_compile src/training_engineering.py scripts/training_engineering_probe.py

echo
echo "unit tests"
PYTHONPATH=src "$PYTHON_BIN" -m unittest discover -s tests -v

echo
echo "PyTorch training engineering probe"
mkdir -p .lab_tmp
PYTHONPATH=src "$PYTHON_BIN" scripts/training_engineering_probe.py --device "$DEVICE" | tee .lab_tmp/run_lab_output.txt
cp .lab_tmp/run_lab_output.txt reports/run_lab_output.txt
rm -rf .lab_tmp

echo
echo "visible result markers"
test -s reports/training_engineering_probe.json
test -s reports/model_card.md
test -s reports/artifact_manifest.json
test -s reports/test_predictions.csv
test -s reports/full_events.jsonl
test -s reports/resume_events.jsonl
test -s reports/checkpoints/best.pt
test -s reports/checkpoints/full_epoch_004.pt
test -s reports/checkpoints/full_final.pt
test -s reports/checkpoints/resume_final.pt
grep -q '"run_status": "ok"' reports/training_engineering_probe.json
grep -q 'CONFIG_HASH_MATCH=yes' reports/run_lab_output.txt
grep -q 'TRAIN_SAMPLES=60' reports/run_lab_output.txt
grep -q 'VAL_SAMPLES=16' reports/run_lab_output.txt
grep -q 'TEST_SAMPLES=14' reports/run_lab_output.txt
grep -q 'MAJORITY_BASELINE_ACC=0.500' reports/run_lab_output.txt
grep -q 'HEURISTIC_BASELINE_ACC=0.786' reports/run_lab_output.txt
grep -q 'FINAL_VAL_ACC=1.000' reports/run_lab_output.txt
grep -q 'FINAL_TEST_ACC=1.000' reports/run_lab_output.txt
grep -q 'BEST_CHECKPOINT_RELOAD_MATCH=yes' reports/run_lab_output.txt
grep -q 'RESUME_MATCHES_FULL_RUN=yes' reports/run_lab_output.txt
grep -q 'JSONL_LOG_ROWS=12' reports/run_lab_output.txt
grep -q 'MODEL_CARD_READY=yes' reports/run_lab_output.txt
grep -q 'ARTIFACT_MANIFEST_READY=yes' reports/run_lab_output.txt
grep -q 'RUN_STATUS=ok' reports/run_lab_output.txt
printf 'probe_ready=reports/training_engineering_probe.json\n'
printf 'model_card_ready=reports/model_card.md\n'
printf 'manifest_ready=reports/artifact_manifest.json\n'
printf 'predictions_ready=reports/test_predictions.csv\n'
printf 'full_events_ready=reports/full_events.jsonl\n'
printf 'resume_events_ready=reports/resume_events.jsonl\n'
printf 'deep_learning_pytorch_training_engineering_lab_status=ok\n'
