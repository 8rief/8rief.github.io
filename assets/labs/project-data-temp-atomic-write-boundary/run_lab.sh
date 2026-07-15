#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT/reports"
python3 -m unittest discover -s "$ROOT/tests" -v
python3 "$ROOT/scripts/data_boundary_probe.py" | tee "$ROOT/reports/run_lab_output.txt"
