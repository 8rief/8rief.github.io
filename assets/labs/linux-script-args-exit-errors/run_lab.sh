#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p reports
python3 scripts/script_error_probe.py | tee reports/run_lab_output.txt
