#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports
python3 -m py_compile src/runtime_metrics_demo.py scripts/metrics_probe.py tests/test_runtime_metrics_demo.py
python3 -m unittest discover -s tests -v | tee reports/test_output.txt
python3 scripts/metrics_probe.py | tee reports/run_lab_output.txt
