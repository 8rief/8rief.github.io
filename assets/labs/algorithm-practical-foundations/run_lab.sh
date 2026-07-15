#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf .lab_tmp
mkdir -p .lab_tmp reports
: > reports/transcript.txt
{
  echo "# Algorithm Practical Foundations Lab Transcript"
  echo "root=$ROOT"
  echo "compiler=$(g++ --version | head -n 1)"
  echo
  echo "## compile"
  g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
    src/algorithm_practical_foundations.cpp \
    -o .lab_tmp/algorithm_practical_foundations
  echo "compiled=.lab_tmp/algorithm_practical_foundations"
  echo
  echo "## run"
  ./.lab_tmp/algorithm_practical_foundations 2>&1 | tee reports/test_output.txt
} | tee -a reports/transcript.txt
