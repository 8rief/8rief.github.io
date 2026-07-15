#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p reports
python3 -m unittest discover -s tests -v
python3 scripts/config_log_probe.py | tee reports/run_lab_output.txt
