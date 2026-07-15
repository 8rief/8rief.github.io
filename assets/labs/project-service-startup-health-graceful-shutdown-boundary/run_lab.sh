#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports
python3 -m py_compile src/service_lifecycle_demo.py scripts/service_probe.py tests/test_service_lifecycle_demo.py
python3 -m unittest discover -s tests -v | tee reports/test_output.txt
python3 scripts/service_probe.py | tee reports/run_lab_output.txt
