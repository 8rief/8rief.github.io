#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf reports
mkdir -p reports
{
  echo '== environment =='
  python3 --version
  /usr/bin/printf --version | head -1
  man --version | head -1
  curl --version | head -1
  echo
  echo '== run documentation probes =='
  python3 scripts/doc_probe.py
  echo
  echo '== generated reports =='
  find reports -maxdepth 1 -type f -printf '%P\n' | sort
} | tee reports/run_lab_output.txt
