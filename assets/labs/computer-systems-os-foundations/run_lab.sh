#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports .lab_tmp
{
  echo "lab=computer-systems-os-foundations"
  echo "pwd=$ROOT"
  echo "python_version=$(python3 --version)"
  echo "kernel=$(uname -srmo)"
  echo
  echo "run systems demo"
  python3 scripts/lab.py
  echo
  echo "metrics summary"
  python3 - <<'PY'
import json
from pathlib import Path
m=json.loads(Path('reports/metrics.json').read_text(encoding='utf-8'))
keys=['data_little_endian','process_child_exit_code','fd_file_bytes_written','vm_page_size','vm_cow_parent_unchanged','thread_controlled_race_actual','thread_mutex_actual','signal_ipc_message','cache_column_to_row_ratio','systems_os_status']
print(json.dumps({k:m[k] for k in keys}, ensure_ascii=False, indent=2, sort_keys=True))
PY
  echo
  echo "run tests"
  python3 -m unittest scripts/test_lab.py
  echo
  echo "visible result markers"
  echo "metrics_ready=reports/metrics.json"
  echo "report_ready=reports/report.md"
  echo "systems_flow_svg_ready=reports/systems_flow.svg"
  echo "memory_process_fd_svg_ready=reports/memory_process_fd.svg"
  echo "cache_locality_svg_ready=reports/cache_locality.svg"
  echo "systems_os_status=ok"
} 2>&1 | tee reports/transcript.txt
