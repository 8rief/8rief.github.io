#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports
exec > >(tee reports/run_lab_output.txt) 2>&1
python3 scripts/cuda_foundations_lab.py
python3 scripts/nqueens_bridge_lab.py
python3 scripts/local_model_agent_lab.py
printf 'column_lab_done\n'
