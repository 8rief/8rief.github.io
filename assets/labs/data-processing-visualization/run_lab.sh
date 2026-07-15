#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 - <<'PY'
from pathlib import Path
import shutil
for name in ["data/raw", "data/processed", "reports"]:
    path = Path(name)
    if path.exists():
        shutil.rmtree(path)
Path("reports").mkdir(parents=True, exist_ok=True)
PY

exec > >(tee reports/transcript.txt) 2>&1

printf 'lab=data-processing-visualization\n'
printf 'pwd=%s\n' "$PWD"
printf 'python_version='; python3 --version

printf '\nsyntax checks\n'
python3 -m py_compile scripts/pipeline.py scripts/test_pipeline.py

printf '\nrun pipeline\n'
python3 scripts/pipeline.py --root .

printf '\nshow raw and cleaned row counts\n'
printf 'raw_csv_lines='; wc -l < data/raw/sales.csv
printf 'clean_csv_lines='; wc -l < data/processed/clean_sales.csv
printf 'reject_csv_lines='; wc -l < data/processed/rejected_sales.csv

printf '\nsummary json\n'
cat reports/summary.json

printf '\nSQLite checks\n'
python3 - <<'PY'
import sqlite3
conn = sqlite3.connect('data/processed/sales.sqlite3')
for row in conn.execute('SELECT region, ROUND(SUM(revenue), 2) AS revenue FROM sales GROUP BY region ORDER BY revenue DESC, region'):
    print(f'region_revenue={row[0]}:{row[1]:.2f}')
print('sqlite_sales_rows=', conn.execute('SELECT COUNT(*) FROM sales').fetchone()[0], sep='')
conn.close()
PY

printf '\nrun tests\n'
PYTHONPATH=scripts python3 -m unittest scripts/test_pipeline.py

printf '\nvisible result markers\n'
printf 'summary_ready=reports/summary.json\n'
printf 'chart_ready=reports/region_revenue.svg\n'
printf 'report_ready=reports/report.md\n'
printf 'pipeline_status=ok\n'
