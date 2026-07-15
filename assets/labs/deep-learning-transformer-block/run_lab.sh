#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=deep-learning-transformer-block"
echo "pwd=$PWD"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/transformer_block.py scripts/transformer_block_probe.py

echo
echo "unit tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "Transformer multi-head and block mechanism probe"
PYTHONPATH=src python3 scripts/transformer_block_probe.py | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/transformer_block_probe.json
test -s reports/transformer_block_report.md
test -s reports/multi_head_trace_table.csv
test -s reports/block_trace_table.csv
grep -q '"run_status": "ok"' reports/transformer_block_probe.json
grep -q 'SINGLE_FIRST_HEAD_ACC=0.500' reports/run_lab_output.txt
grep -q 'SINGLE_SECOND_HEAD_ACC=0.500' reports/run_lab_output.txt
grep -q 'SINGLE_BLEND_HEAD_ACC=0.750' reports/run_lab_output.txt
grep -q 'MULTI_HEAD_PAIR_ACC=1.000' reports/run_lab_output.txt
grep -q 'MULTI_HEAD_GAIN_OVER_BEST_BASELINE=0.250' reports/run_lab_output.txt
grep -q 'MULTI_HEAD_MIN_TOP_WEIGHT=0.968' reports/run_lab_output.txt
grep -q 'HEADS_FOCUS_DIFFERENT_KEYS=yes' reports/run_lab_output.txt
grep -q 'NO_ATTENTION_BLOCK_ACC=0.500' reports/run_lab_output.txt
grep -q 'NO_RESIDUAL_BLOCK_ACC=0.500' reports/run_lab_output.txt
grep -q 'ATTENTION_RESIDUAL_FFN_ACC=1.000' reports/run_lab_output.txt
grep -q 'BLOCK_GAIN_OVER_BEST_BASELINE=0.500' reports/run_lab_output.txt
grep -q 'LAYER_NORM_MEAN_OK=yes' reports/run_lab_output.txt
grep -q 'LAYER_NORM_RMS_OK=yes' reports/run_lab_output.txt
printf 'probe_ready=reports/transformer_block_probe.json\n'
printf 'report_ready=reports/transformer_block_report.md\n'
printf 'multi_head_trace_ready=reports/multi_head_trace_table.csv\n'
printf 'block_trace_ready=reports/block_trace_table.csv\n'
printf 'deep_learning_transformer_block_lab_status=ok\n'
