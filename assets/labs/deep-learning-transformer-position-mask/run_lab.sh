#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=deep-learning-transformer-position-mask"
echo "pwd=$PWD"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/position_mask.py scripts/position_mask_probe.py

echo
echo "unit tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "Transformer position and causal-mask mechanism probe"
PYTHONPATH=src python3 scripts/position_mask_probe.py | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/position_mask_probe.json
test -s reports/position_mask_report.md
test -s reports/order_trace_table.csv
test -s reports/future_trace_table.csv
grep -q '"run_status": "ok"' reports/position_mask_probe.json
grep -q 'POSITION_BAG_BASELINE_ACC=0.500' reports/run_lab_output.txt
grep -q 'NO_POSITION_ATTENTION_ACC=0.500' reports/run_lab_output.txt
grep -q 'POSITIONAL_ATTENTION_ACC=1.000' reports/run_lab_output.txt
grep -q 'POSITION_GAIN_OVER_BEST_BASELINE=0.500' reports/run_lab_output.txt
grep -q 'POSITION_MIN_TOP_WEIGHT=0.944' reports/run_lab_output.txt
grep -q 'UNMASKED_FUTURE_LOOKUP_ACC=1.000' reports/run_lab_output.txt
grep -q 'CAUSAL_MASKED_LOOKUP_ACC=0.500' reports/run_lab_output.txt
grep -q 'MASK_BLOCKS_FUTURE=yes' reports/run_lab_output.txt
printf 'probe_ready=reports/position_mask_probe.json\n'
printf 'report_ready=reports/position_mask_report.md\n'
printf 'order_trace_ready=reports/order_trace_table.csv\n'
printf 'future_trace_ready=reports/future_trace_table.csv\n'
printf 'deep_learning_transformer_position_mask_lab_status=ok\n'
