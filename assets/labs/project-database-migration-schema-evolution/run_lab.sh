#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

rm -rf reports __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
mkdir -p reports

echo "lab=project-database-migration-schema-evolution"
echo "pwd=$PWD"
echo "python_version=$(python3 --version)"

echo
echo "syntax check"
python3 -m py_compile src/migration_demo.py scripts/migration_probe.py

echo
echo "migration tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo
echo "migration probe"
PYTHONPATH=src python3 scripts/migration_probe.py | tee reports/run_lab_output.txt

echo
echo "visible result markers"
test -s reports/migration_probe.json
test -s reports/migration_report.md
test -s reports/schema_after_v3.sql
grep -q 'SCHEMA_VERSION=3' reports/run_lab_output.txt
grep -q 'UNIQUE_INDEX_PRESENT=yes' reports/run_lab_output.txt
grep -q 'DUPLICATE_PREFLIGHT_FAILED=yes' reports/run_lab_output.txt
grep -q 'RUN_STATUS=ok' reports/run_lab_output.txt
printf 'probe_ready=reports/migration_probe.json\n'
printf 'report_ready=reports/migration_report.md\n'
printf 'schema_ready=reports/schema_after_v3.sql\n'
printf 'database_migration_lab_status=ok\n'
