#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="$LAB_DIR/reports"
WORKSPACE_DIR="$LAB_DIR/workspace"
TRANSCRIPT="$REPORT_DIR/transcript.txt"

rm -rf "$REPORT_DIR" "$WORKSPACE_DIR"
mkdir -p "$REPORT_DIR" "$WORKSPACE_DIR"

run() {
  printf '\n$ %s\n' "$*" | tee -a "$TRANSCRIPT"
  bash -lc "$*" 2>&1 | tee -a "$TRANSCRIPT"
}

{
  echo "# OS/Linux process-file foundations lab transcript"
  echo "date_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "kernel=$(uname -srmo)"
  echo "python=$(python3 --version)"
  echo "bash=$($BASH --version | head -n 1)"
  echo "lab_dir=$LAB_DIR"
} > "$TRANSCRIPT"

run "cd '$LAB_DIR' && python3 -m unittest discover -s tests -v"
run "cd '$LAB_DIR' && python3 src/system_observer.py --workspace '$WORKSPACE_DIR' --outdir '$REPORT_DIR'"
run "cd '$LAB_DIR' && find workspace -maxdepth 3 -type f -print | sort"
run "cd '$LAB_DIR' && ls -li workspace/files"
run "cd '$LAB_DIR' && stat -c '%n inode=%i type=%F mode=%A uid=%u gid=%g size=%s' workspace/files/alpha.txt workspace/logs/events.log"
run "cd '$LAB_DIR' && python3 -c 'import sys; print(\"stdout line\"); print(\"stderr line\", file=sys.stderr)' > workspace/generated/stdout.txt 2> workspace/generated/stderr.txt && printf 'stdout=' && cat workspace/generated/stdout.txt && printf 'stderr=' && cat workspace/generated/stderr.txt"
run "ps -o pid,ppid,stat,comm -p $$"
run "cd '$LAB_DIR' && OS_LAB_DEMO=visible python3 -c 'import os; print(os.environ.get(\"OS_LAB_DEMO\"))'"
run "cd '$LAB_DIR' && grep -E '^(INFO|WARN|ERROR)' workspace/logs/events.log | awk '{print \$1}' | sort | uniq -c"
run "cd '$LAB_DIR' && sed -n '1,220p' reports/system_observer_report.md"

printf '\nTranscript saved to %s\n' "$TRANSCRIPT" | tee -a "$TRANSCRIPT"
