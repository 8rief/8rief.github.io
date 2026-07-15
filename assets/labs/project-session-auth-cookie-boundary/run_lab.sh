#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=project-session-auth-cookie-boundary"
echo "pwd=$PWD"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/session_auth_demo.py scripts/session_auth_probe.py

echo
echo "unit/integration tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "session auth probe"
PYTHONPATH=src python3 scripts/session_auth_probe.py | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/session_auth_probe.json
test -s reports/session_auth_report.md
test -s reports/session_events.jsonl
grep -q '"login_status": 200' reports/session_auth_probe.json
grep -q '"forged_cookie_rejected": true' reports/session_auth_probe.json
grep -q '"csrf_required": true' reports/session_auth_probe.json
grep -q '"admin_allowed": true' reports/session_auth_probe.json
grep -q 'RUN_STATUS=ok' reports/run_lab_output.txt
printf 'probe_ready=reports/session_auth_probe.json\n'
printf 'events_ready=reports/session_events.jsonl\n'
printf 'report_ready=reports/session_auth_report.md\n'
printf 'session_auth_lab_status=ok\n'
