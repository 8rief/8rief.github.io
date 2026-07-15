#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=project-http-api-contract-boundary"
echo "pwd=$PWD"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/http_api_demo.py scripts/api_contract_probe.py

echo
echo "unit/integration tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "contract probe"
PYTHONPATH=src python3 scripts/api_contract_probe.py | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/api_contract_probe.json
test -s reports/api_contract_report.md
test -s reports/api_events.jsonl
grep -q '"create_status": 201' reports/api_contract_probe.json
grep -q '"conflict_status": 409' reports/api_contract_probe.json
grep -q '"not_found_status": 404' reports/api_contract_probe.json
grep -q 'RUN_STATUS=ok' reports/run_lab_output.txt
printf 'probe_ready=reports/api_contract_probe.json\n'
printf 'events_ready=reports/api_events.jsonl\n'
printf 'report_ready=reports/api_contract_report.md\n'
printf 'http_api_contract_lab_status=ok\n'
