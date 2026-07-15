#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports www
TRANSCRIPT="$ROOT/reports/transcript.txt"
LOG="$ROOT/reports/path.log"
PORT=18185
: > "$TRANSCRIPT"
run() { printf '\n$ %s\n' "$*" | tee -a "$TRANSCRIPT"; "$@" 2>&1 | tee -a "$TRANSCRIPT"; }
run_shell() { printf '\n$ %s\n' "$*" | tee -a "$TRANSCRIPT"; bash -lc "$*" 2>&1 | tee -a "$TRANSCRIPT"; }
cleanup() { if [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" 2>/dev/null; then kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; fi; }
trap cleanup EXIT

printf 'public file inside web root\n' > www/index.txt
printf 'SECRET outside web root - local lab only\n' > secret.txt
run python3 --version
run_shell "find . -maxdepth 2 -type f | sort"
python3 path_server.py --host 127.0.0.1 --port "$PORT" --web-root www --log "$LOG" &
SERVER_PID=$!
sleep 0.3
run_shell "ss -ltnp | grep ':$PORT'"
run curl --noproxy '*' -sS "http://127.0.0.1:$PORT/unsafe?name=index.txt"
run curl --noproxy '*' -sS "http://127.0.0.1:$PORT/unsafe?name=../secret.txt"
run curl --noproxy '*' -sS "http://127.0.0.1:$PORT/safe?name=../secret.txt"
run curl --noproxy '*' -sS "http://127.0.0.1:$PORT/safe?name=index.txt"
run cat "$LOG"
printf '\nTranscript saved to %s\n' "$TRANSCRIPT" | tee -a "$TRANSCRIPT"
