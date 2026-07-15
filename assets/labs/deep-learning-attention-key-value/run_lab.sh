#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=deep-learning-attention-key-value"
echo "pwd=$PWD"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/attention_lookup.py scripts/attention_probe.py

echo
echo "unit tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "attention key-value lookup mechanism probe"
PYTHONPATH=src python3 scripts/attention_probe.py | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/attention_probe.json
test -s reports/attention_report.md
test -s reports/trace_table.csv
grep -q '"run_status": "ok"' reports/attention_probe.json
grep -q 'MAJORITY_BASELINE_ACC=0.250' reports/run_lab_output.txt
grep -q 'LAST_VALUE_ACC=0.250' reports/run_lab_output.txt
grep -q 'BAG_OF_VALUES_ACC=0.250' reports/run_lab_output.txt
grep -q 'FIXED_SUMMARY_ACC=0.250' reports/run_lab_output.txt
grep -q 'ATTENTION_LOOKUP_ACC=1.000' reports/run_lab_output.txt
grep -q 'ATTENTION_GAIN_OVER_BEST_BASELINE=0.750' reports/run_lab_output.txt
grep -q 'ATTENTION_MIN_TOP_WEIGHT=0.711' reports/run_lab_output.txt
grep -q 'TOP_KEYS_MATCH_QUERY=yes' reports/run_lab_output.txt
printf 'probe_ready=reports/attention_probe.json\n'
printf 'report_ready=reports/attention_report.md\n'
printf 'trace_table_ready=reports/trace_table.csv\n'
printf 'deep_learning_attention_lab_status=ok\n'
