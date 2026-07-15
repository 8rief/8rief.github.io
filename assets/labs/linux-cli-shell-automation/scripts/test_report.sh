#!/usr/bin/env bash
set -euo pipefail

report_dir=${1:-reports}

require_line() {
  local pattern=$1
  local file=$2
  if ! grep -Fq "$pattern" "$file"; then
    printf 'missing pattern %q in %s\n' "$pattern" "$file" >&2
    exit 1
  fi
}

require_line 'total_requests=16' "$report_dir/summary.txt"
require_line 'error_requests=5' "$report_dir/summary.txt"
require_line 'slow_requests_ge_400ms=4' "$report_dir/summary.txt"
require_line $'200	8' "$report_dir/status_counts.tsv"
require_line $'/jobs/payment	570.0	2' "$report_dir/path_latency.tsv"
require_line $'api	ERROR	3' "$report_dir/service_level_counts.tsv"
require_line $'worker	ERROR	1' "$report_dir/service_level_counts.tsv"
require_line $'app 2026-07-02.log	8	3' "$report_dir/batch-summary.tsv"

printf 'shell_lab_tests=ok\n'
