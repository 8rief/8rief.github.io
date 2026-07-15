#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf reports lab_bins
mkdir -p reports lab_bins
{
  echo '== environment =='
  bash --version | head -1
  dpkg-query --version | head -1
  apt-cache --version | head -1
  python3 --version
  echo
  echo '== run PATH and package probes =='
  python3 scripts/package_path_probe.py
  echo
  echo '== selected evidence =='
  python3 - <<'PY'
import json
from pathlib import Path
rows=json.loads(Path('reports/package_path_probe.json').read_text(encoding='utf-8'))
for name in ['path-order-first','path-order-second','execute-bit-boundary','package-owner','package-version-policy']:
    row=next(r for r in rows if r['name']==name)
    print(name, 'PASS' if row['ok'] else 'FAIL', row['first_lines'][:3])
PY
  echo
  echo '== generated reports =='
  find reports -maxdepth 1 -type f -printf '%P\n' | sort
} | tee reports/run_lab_output.txt
