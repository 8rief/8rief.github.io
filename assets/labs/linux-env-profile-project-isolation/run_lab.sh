#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf reports
mkdir -p reports
{
  echo '== environment =='
  bash --version | head -1
  env --version | head -1
  python3 --version
  echo
  echo '== run env/profile probes =='
  python3 scripts/env_profile_probe.py
  echo
  echo '== selected evidence =='
  python3 - <<'PY'
import json
from pathlib import Path
rows=json.loads(Path('reports/env_profile_probe.json').read_text(encoding='utf-8'))
for name in ['local-variable-not-inherited','exported-variable-inherited','interactive-bashrc','project-env-source','subshell-does-not-leak-upward']:
    row=next(r for r in rows if r['name']==name)
    print(name, 'PASS' if row['ok'] else 'FAIL', row['first_lines'][:4])
PY
  echo
  echo '== generated reports =='
  find reports -maxdepth 1 -type f -printf '%P\n' | sort
} | tee reports/run_lab_output.txt
