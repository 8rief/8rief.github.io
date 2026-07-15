#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 - <<'PY'
from pathlib import Path
import shutil
for name in ["data", "reports"]:
    path = Path(name)
    if path.exists():
        shutil.rmtree(path)
Path("reports").mkdir(parents=True, exist_ok=True)
PY

exec > >(tee reports/transcript.txt) 2>&1

printf 'lab=database-cache-practice\n'
printf 'pwd=%s\n' "$PWD"
printf 'python_version='; python3 --version

printf '\nsyntax checks\n'
python3 -m py_compile scripts/app.py scripts/test_app.py

printf '\nrun demo\n'
python3 scripts/app.py --root .

printf '\nsummary json\n'
cat reports/summary.json

printf '\nSQLite verification\n'
python3 - <<'PY'
import sqlite3
conn = sqlite3.connect('data/app.sqlite3')
conn.row_factory = sqlite3.Row
print('sqlite_product_rows=', conn.execute('SELECT COUNT(*) FROM products').fetchone()[0], sep='')
print('sqlite_order_rows=', conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0], sep='')
print('sqlite_order_item_rows=', conn.execute('SELECT COUNT(*) FROM order_items').fetchone()[0], sep='')
for row in conn.execute('EXPLAIN QUERY PLAN SELECT sku, name FROM products WHERE category = ? ORDER BY sku', ('gear',)):
    print('query_plan=', row[3], sep='')
conn.close()
PY

printf '\nrun tests\n'
PYTHONPATH=scripts python3 -m unittest scripts/test_app.py

printf '\nvisible result markers\n'
printf 'summary_ready=reports/summary.json\n'
printf 'chart_ready=reports/category_revenue.svg\n'
printf 'report_ready=reports/report.md\n'
printf 'database_cache_status=ok\n'
