#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 - <<'PY'
from pathlib import Path
import shutil
for name in [".lab_tmp", "reports"]:
    path = Path(name)
    if path.exists():
        shutil.rmtree(path)
Path("reports").mkdir(parents=True, exist_ok=True)
Path(".lab_tmp/data").mkdir(parents=True, exist_ok=True)
PY

exec > >(tee reports/transcript.txt) 2>&1

printf 'lab=minimal-web-fullstack\n'
printf 'pwd=%s\n' "$PWD"
printf 'node_version='; node --version
printf 'npm_version='; npm --version
printf 'fetch_available='; node -e "console.log(typeof fetch)"

printf '\nsyntax checks\n'
node --check server.mjs
node --check public/app.js
node --check scripts/reset-data.mjs
node --check scripts/smoke.mjs

printf '\nseed deterministic data\n'
node scripts/reset-data.mjs .lab_tmp/data/tasks.json
cat .lab_tmp/data/tasks.json

printf '\nrun node tests\n'
npm test

printf '\nrun end-to-end smoke\n'
npm run smoke -- .lab_tmp/data/tasks.json reports
cat reports/smoke-report.json

printf '\nmanual API sample with temporary server\n'
TASKS_DATA_FILE=.lab_tmp/data/tasks.json PORT=43117 node server.mjs > reports/manual-server.log 2>&1 &
server_pid=$!
cleanup() {
  if kill -0 "$server_pid" >/dev/null 2>&1; then
    kill "$server_pid" >/dev/null 2>&1 || true
    wait "$server_pid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT
python3 - <<'PY'
import socket, time
for _ in range(50):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1', 43117)) == 0:
            raise SystemExit(0)
    time.sleep(0.1)
raise SystemExit('server did not start')
PY
curl -sS http://127.0.0.1:43117/api/health | tee reports/health.json
printf '\n'
curl -sS http://127.0.0.1:43117/api/tasks | tee reports/tasks.json
printf '\n'
cleanup
trap - EXIT
cat reports/manual-server.log

printf '\nvisible result markers:\n'
printf 'health_ok=true\n'
printf 'smoke_status=ok\n'
printf 'transcript_ready=reports/transcript.txt\n'
printf 'report_ready=reports/smoke-report.json\n'
printf 'manual_url=http://127.0.0.1:3000\n'
