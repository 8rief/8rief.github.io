#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf .lab_tmp
mkdir -p .lab_tmp reports
: > reports/transcript.txt
{
  echo "# SQL Practical Development Lab Transcript"
  echo "root=$ROOT"
  echo "python=$(python3 --version 2>&1)"
  python3 - <<'PY'
import sqlite3
print(f"sqlite={sqlite3.sqlite_version}")
PY
  echo
  echo "## unittest"
  python3 -m unittest discover -s tests -v 2>&1 | tee reports/test_output.txt
  echo
  echo "## capstone run-all"
  python3 src/sql_practical_lab.py run-all \
    --db .lab_tmp/tickets.db \
    --reports reports \
    --import-csv sample_import/new_tickets.csv 2>&1 | tee reports/demo_output.txt
  echo
  echo "## query open_tickets"
  python3 src/sql_practical_lab.py query --db .lab_tmp/tickets.db --name open_tickets
  echo
  echo "## explain"
  python3 src/sql_practical_lab.py explain --db .lab_tmp/tickets.db
} | tee -a reports/transcript.txt
