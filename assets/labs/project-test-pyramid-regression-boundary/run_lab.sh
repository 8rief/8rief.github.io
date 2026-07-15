#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports
rm -f reports/*.json reports/*.jsonl reports/*.md reports/*.txt reports/bad_orders.csv reports/bad_summary.json reports/bad_events.jsonl
TRANSCRIPT="reports/run_lab_output.txt"
exec > >(tee "$TRANSCRIPT") 2>&1

echo "lab=project-test-pyramid-regression-boundary"
echo "pwd=$ROOT"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/test_pyramid_demo.py scripts/regression_probe.py tests/test_unit_pricing.py tests/test_integration_pipeline.py tests/test_smoke_cli.py

echo
echo "unit/integration/smoke tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "regression probe"
PYTHONPATH=src python3 scripts/regression_probe.py

echo
echo "visible result markers"
echo "probe_ready=reports/test_pyramid_probe.json"
echo "summary_ready=reports/summary.json"
echo "events_ready=reports/events.jsonl"
echo "report_ready=reports/test_pyramid_report.md"
echo "test_pyramid_lab_status=ok"
