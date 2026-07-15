#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf reports
mkdir -p reports

cleanup() {
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

wait_http() {
  local url="$1"
  python3 - "$url" <<'PYWAIT'
import sys, time, urllib.request
url = sys.argv[1]
for _ in range(80):
    try:
        with urllib.request.urlopen(url, timeout=0.3) as response:
            if response.status == 200:
                print(f"ready {url} status={response.status}")
                raise SystemExit(0)
    except Exception:
        time.sleep(0.1)
print(f"not ready: {url}", file=sys.stderr)
raise SystemExit(1)
PYWAIT
}

{
  echo "== environment =="
  rustc --version
  cargo --version

  echo "== format =="
  cargo fmt -- --check

  echo "== tests =="
  cargo test

  echo "== clippy =="
  cargo clippy --all-targets -- -D warnings

  echo "== build =="
  cargo build

  echo "== CLI summarize =="
  ./target/debug/rust-log-insight-cli \
    --config sample_config/log-insight.toml \
    summarize \
    --input sample_logs/app.log \
    --json reports/summary.json \
    --csv reports/events.csv
  python3 -m json.tool reports/summary.json | sed -n '1,120p'
  echo "-- csv --"
  sed -n '1,12p' reports/events.csv

  echo "== start local API =="
  ./target/debug/rust-log-insight-cli \
    --config sample_config/log-insight.toml \
    serve \
    --input sample_logs/app.log \
    --addr 127.0.0.1:18220 > reports/api-server.log 2>&1 &
  API_PID=$!
  wait_http http://127.0.0.1:18220/health

  echo "== API smoke =="
  python3 - <<'PYSMOKE'
import json, urllib.request
for url in ["http://127.0.0.1:18220/health", "http://127.0.0.1:18220/api/summary", "http://127.0.0.1:18220/api/events"]:
    with urllib.request.urlopen(url, timeout=2) as response:
        body = response.read().decode()
        print(url, response.status)
        print(json.dumps(json.loads(body), ensure_ascii=False, indent=2)[:1400])
PYSMOKE

  echo "== help =="
  ./target/debug/rust-log-insight-cli --help | sed -n '1,80p'

  echo "== done =="
} | tee reports/transcript.txt
