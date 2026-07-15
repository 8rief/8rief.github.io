#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports
exec > >(tee reports/run_lab_output.txt) 2>&1

echo "== CUDA/local AI foundations lab =="
python3 scripts/gpu_env_probe.py --output reports/gpu_env_probe.json --markdown reports/gpu_env_report.md
python3 scripts/roadmap_matrix.py --json reports/cuda_local_ai_roadmap.json --markdown reports/cuda_local_ai_roadmap.md

echo "== artifacts =="
ls -1 reports
