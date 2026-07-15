#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf .lab_tmp
mkdir -p .lab_tmp reports
: > reports/transcript.txt
{
  echo "# Debug and Build Tooling Foundations Lab Transcript"
  echo "root=$ROOT"
  echo "compiler=$(g++ --version | head -n 1)"
  echo "cmake=$(cmake --version | head -n 1)"
  echo "ninja=$(ninja --version)"
  if command -v gdb >/dev/null 2>&1; then echo "gdb=$(gdb --version | head -n 1)"; else echo "gdb=not-installed"; fi
  echo
  echo "## configure Debug"
  cmake -S . -B .lab_tmp/build-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
  echo
  echo "## build Debug"
  cmake --build .lab_tmp/build-debug
  echo
  echo "## ctest"
  ctest --test-dir .lab_tmp/build-debug --output-on-failure 2>&1 | tee reports/test_output.txt
  echo
  echo "## CLI parse/log/shrink/timing"
  ./.lab_tmp/build-debug/debug_lab_cli parse 10 5
  ./.lab_tmp/build-debug/debug_lab_cli shrink
  ./.lab_tmp/build-debug/debug_lab_cli log
  /usr/bin/time -f 'time_elapsed=%e max_rss_kb=%M' ./.lab_tmp/build-debug/debug_lab_cli timing 200000 2>&1 | tee reports/timing_output.txt
  echo
  echo "## Ninja targets"
  ninja -C .lab_tmp/build-debug -t targets | tee reports/build_targets.txt
  echo
  echo "## symbol evidence"
  nm -C .lab_tmp/build-debug/debug_lab_cli | grep 'buglab::running_mean' | tee reports/symbol_output.txt
  SYMBOL_ADDR="$(nm -C .lab_tmp/build-debug/debug_lab_cli | awk '/buglab::running_mean/ {print $1; exit}')"
  if [[ -n "${SYMBOL_ADDR:-}" ]]; then
    addr2line -f -C -e .lab_tmp/build-debug/debug_lab_cli "0x${SYMBOL_ADDR}" | tee -a reports/symbol_output.txt
  fi
  echo
  echo "## configure sanitizer"
  cmake -S . -B .lab_tmp/build-sanitize -G Ninja -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON
  cmake --build .lab_tmp/build-sanitize
  echo
  echo "## sanitizer evidence"
  set +e
  ./.lab_tmp/build-sanitize/debug_lab_cli unsafe-index > reports/sanitizer_output.txt 2>&1
  ASAN_STATUS=$?
  ./.lab_tmp/build-sanitize/debug_lab_cli ubsan-overflow >> reports/sanitizer_output.txt 2>&1
  UBSAN_STATUS=$?
  set -e
  echo "asan_status=$ASAN_STATUS ubsan_status=$UBSAN_STATUS"
  grep -E 'AddressSanitizer|runtime error' reports/sanitizer_output.txt | head -n 6
  echo
  echo "## report"
  cat > reports/debug_build_report.md <<EOF
# Debug and Build Tooling Foundations Lab Report

- compiler: $(g++ --version | head -n 1)
- cmake: $(cmake --version | head -n 1)
- ninja: $(ninja --version)
- gdb: $(command -v gdb >/dev/null 2>&1 && gdb --version | head -n 1 || echo not-installed)
- tests: see reports/test_output.txt
- sanitizer statuses: ASan=$ASAN_STATUS UBSan=$UBSAN_STATUS
- timing: see reports/timing_output.txt
- build targets: see reports/build_targets.txt
- symbol evidence: see reports/symbol_output.txt
EOF
  echo "report=reports/debug_build_report.md"
} | tee -a reports/transcript.txt
