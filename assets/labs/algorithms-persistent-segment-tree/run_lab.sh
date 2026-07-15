#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports
TRANSCRIPT="$ROOT/reports/transcript.txt"
: > "$TRANSCRIPT"
run() { printf '
$ %s
' "$*" | tee -a "$TRANSCRIPT"; "$@" 2>&1 | tee -a "$TRANSCRIPT"; }
run g++ --version
run cmake --version
run ninja --version
rm -rf build
run cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
run cmake --build build
run ctest --test-dir build --output-on-failure
run ./build/persistent_segment_tree_demo
printf '
Transcript saved to %s
' "$TRANSCRIPT" | tee -a "$TRANSCRIPT"
