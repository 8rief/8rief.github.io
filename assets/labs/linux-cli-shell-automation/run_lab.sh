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
Path(".lab_tmp/logs").mkdir(parents=True, exist_ok=True)
PY

exec > >(tee reports/transcript.txt) 2>&1

printf 'lab=linux-cli-shell-automation\n'
printf 'pwd=%s\n' "$PWD"
printf 'bash_version=%s\n' "${BASH_VERSION:-unknown}"
printf 'grep_version='; (grep --version 2>/dev/null || true) | head -n 1
printf 'awk_version='; (awk --version 2>/dev/null || awk -W version 2>/dev/null || true) | head -n 1
printf 'sed_version='; (sed --version 2>/dev/null || true) | head -n 1
find --version 2>/dev/null | head -n 1 || true

bash scripts/generate_logs.sh .lab_tmp/logs
printf '\ncreated log files:\n'
find .lab_tmp/logs -type f -name '*.log' -print | sort

printf '\nmanual command: total lines per file\n'
wc -l .lab_tmp/logs/*.log

printf '\nmanual command: ERROR lines and count\n'
grep -h ' level=ERROR ' .lab_tmp/logs/*.log | tee reports/errors.log
printf 'manual_error_count=%s\n' "$(wc -l < reports/errors.log | tr -d ' ')"

printf '\nmanual command: status counts\n'
awk '{ for (i=1; i<=NF; i++) { split($i, kv, "="); if (kv[1] == "status") print kv[2] } }' .lab_tmp/logs/*.log | sort | uniq -c | sort -k1,1nr -k2,2

printf '\nrun reusable report script\n'
bash scripts/report.sh .lab_tmp/logs reports
cat reports/summary.txt

printf '\nrun safe batch script with find -print0\n'
bash scripts/safe_batch.sh .lab_tmp/logs reports/batch-summary.tsv
cat reports/batch-summary.tsv

printf '\nrun tests\n'
bash -n scripts/*.sh
bash scripts/test_report.sh reports

if command -v shellcheck >/dev/null 2>&1; then
  shellcheck run_lab.sh scripts/*.sh
  printf 'shellcheck=ok\n'
else
  printf 'shellcheck=skipped_not_installed\n'
fi

printf '\nvisible result markers:\n'
printf 'report_ready=reports/summary.txt\n'
printf 'transcript_ready=reports/transcript.txt\n'
printf 'batch_summary_ready=reports/batch-summary.tsv\n'
printf 'test_status=ok\n'
