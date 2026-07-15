#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

step="${1:-all}"
case "$step" in
  08-local-qwen)
    exec "${AGENT_PYTHON:-$ROOT/.venv/bin/python}" scripts/local_qwen.py ask \
      --question "vector_add_ok 为什么不是性能证据？" --rag
    ;;
  09-domain-lora)
    exec "${AGENT_PYTHON:-$ROOT/.venv/bin/python}" scripts/train_domain_lora.py
    ;;
  *)
    exec python3 scripts/course.py "$step"
    ;;
esac
