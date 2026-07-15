#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=deep-learning-lstm-gru-gates"
echo "pwd=$PWD"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/gated_memory.py scripts/gate_probe.py

echo
echo "unit tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "LSTM/GRU gate memory mechanism probe"
PYTHONPATH=src python3 scripts/gate_probe.py | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/gate_probe.json
test -s reports/gate_report.md
test -s reports/trace_table.csv
grep -q '"run_status": "ok"' reports/gate_probe.json
grep -q 'MAJORITY_BASELINE_ACC=0.500' reports/run_lab_output.txt
grep -q 'LAST_TOKEN_ACC=0.500' reports/run_lab_output.txt
grep -q 'VANILLA_RNN_ACC=0.500' reports/run_lab_output.txt
grep -q 'LSTM_GATE_ACC=1.000' reports/run_lab_output.txt
grep -q 'GRU_UPDATE_GATE_ACC=1.000' reports/run_lab_output.txt
grep -q 'GATE_GAIN_OVER_BEST_BASELINE=0.500' reports/run_lab_output.txt
grep -q 'LSTM_CELL_STABLE=yes' reports/run_lab_output.txt
grep -q 'GRU_KEEP_STABLE=yes' reports/run_lab_output.txt
printf 'probe_ready=reports/gate_probe.json\n'
printf 'report_ready=reports/gate_report.md\n'
printf 'trace_table_ready=reports/trace_table.csv\n'
printf 'deep_learning_lstm_gru_lab_status=ok\n'
