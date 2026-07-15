#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=deep-learning-cnn-foundations"
echo "pwd=$PWD"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/cnn_from_scratch.py scripts/cnn_probe.py

echo
echo "unit tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "cnn mechanism probe"
PYTHONPATH=src python3 scripts/cnn_probe.py | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/cnn_probe.json
test -s reports/cnn_report.md
test -s reports/feature_table.csv
grep -q '"conv_feature_accuracy": 1.0' reports/cnn_probe.json
grep -q '"run_status": "ok"' reports/cnn_probe.json
grep -q 'CONV_FEATURE_ACC=1.000' reports/run_lab_output.txt
grep -q 'SHIFT_GENERALIZATION_GAIN=1.000' reports/run_lab_output.txt
printf 'probe_ready=reports/cnn_probe.json\n'
printf 'report_ready=reports/cnn_report.md\n'
printf 'feature_table_ready=reports/feature_table.csv\n'
printf 'deep_learning_cnn_lab_status=ok\n'
