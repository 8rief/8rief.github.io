#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf .lab_tmp
mkdir -p .lab_tmp reports
: > reports/transcript.txt
{
  echo "# Computer Network Foundations Lab Transcript"
  echo "root=$ROOT"
  echo "python=$(python3 --version)"
  echo "kernel=$(uname -sr)"
  echo "ip=$(command -v ip || echo not-found)"
  echo "ss=$(command -v ss || echo not-found)"
  echo "curl=$(command -v curl || echo not-found)"
  echo "getent=$(command -v getent || echo not-found)"
  echo
  echo "## run netlab"
  PYTHONPATH=. python3 src/netlab.py run --reports reports
  echo
  echo "## unittest"
  PYTHONPATH=. python3 -m unittest discover -s tests -v 2>&1
  echo
  echo "## report head"
  sed -n '1,80p' reports/network_report.md
} | tee -a reports/transcript.txt
