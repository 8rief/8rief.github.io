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
  echo "# Git foundations and collaboration lab transcript"
  echo "date_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "kernel=$(uname -srmo)"
  echo "python=$(python3 --version)"
  echo "git=$(git --version)"
  echo "lab_dir=$LAB_DIR"
} > "$TRANSCRIPT"

run "cd '$LAB_DIR' && python3 -m unittest discover -s tests -v"
run "cd '$LAB_DIR' && python3 src/git_lab.py --workspace '$WORKSPACE_DIR' --outdir '$REPORT_DIR'"
run "cd '$LAB_DIR/workspace/project' && git status --short"
run "cd '$LAB_DIR/workspace/project' && git log --oneline --graph --decorate --all -n 12"
run "cd '$LAB_DIR/workspace/project' && git cat-file -t HEAD && git cat-file -t HEAD^{tree}"
run "cd '$LAB_DIR/workspace/project' && git ls-tree --name-only HEAD"
run "cd '$LAB_DIR/workspace/project' && git show --stat --oneline --decorate HEAD"
run "cd '$LAB_DIR/workspace/project' && git tag --list --sort=creatordate"
run "cd '$LAB_DIR' && sed -n '1,240p' reports/git_foundations_report.md"

printf '\nTranscript saved to %s\n' "$TRANSCRIPT" | tee -a "$TRANSCRIPT"
