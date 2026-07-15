#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=deep-learning-rnn-hidden-state"
echo "pwd=$PWD"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/rnn_hidden_state.py scripts/rnn_probe.py

echo
echo "unit tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "rnn hidden-state mechanism probe"
PYTHONPATH=src python3 scripts/rnn_probe.py | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/rnn_probe.json
test -s reports/rnn_report.md
test -s reports/trace_table.csv
grep -q '"rnn_memory_accuracy": 1.0' reports/rnn_probe.json
grep -q '"run_status": "ok"' reports/rnn_probe.json
grep -q 'MAJORITY_BASELINE_ACC=0.500' reports/run_lab_output.txt
grep -q 'LAST_TOKEN_ACC=0.500' reports/run_lab_output.txt
grep -q 'SUFFIX_BAG_ACC=0.500' reports/run_lab_output.txt
grep -q 'NO_RECURRENCE_ACC=0.500' reports/run_lab_output.txt
grep -q 'RNN_MEMORY_ACC=1.000' reports/run_lab_output.txt
grep -q 'MEMORY_GAIN_OVER_BEST_BASELINE=0.500' reports/run_lab_output.txt
printf 'probe_ready=reports/rnn_probe.json\n'
printf 'report_ready=reports/rnn_report.md\n'
printf 'trace_table_ready=reports/trace_table.csv\n'
printf 'deep_learning_rnn_lab_status=ok\n'
