#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports
TRANSCRIPT="$ROOT/reports/transcript.txt"
{
  echo "# Local Evidence Kit lab transcript"
  date '+timestamp=%Y-%m-%d %H:%M:%S %z'
  echo "root=$ROOT"
  python3 --version
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -e ".[dev]"
  python -m pytest -q
  rm -f reports/sample-manifest.json reports/sample-manifest.csv
  python -m local_evidence.cli scan sample_data --json reports/sample-manifest.json --csv reports/sample-manifest.csv
  python -m local_evidence.cli summary reports/sample-manifest.json
  python scripts/api_smoke.py
  python scripts/http_client_smoke.py
  echo "--- JSON excerpt ---"
  python - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('reports/sample-manifest.json').read_text(encoding='utf-8'))
print(json.dumps({
    'root_name': payload['root_name'],
    'summary': payload['summary'],
    'first_entry': payload['entries'][0],
}, ensure_ascii=False, indent=2, sort_keys=True))
PY
} 2>&1 | tee "$TRANSCRIPT"
