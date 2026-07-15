#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports

{
  echo "== unit tests =="
  python3 -m unittest discover -s tests -v
  echo "== deterministic learner course =="
  ./learn.sh all
  echo "LOCAL_AGENT_LAB_OK cpu_steps=8 tests=8"
} | tee reports/run_lab_output.txt
