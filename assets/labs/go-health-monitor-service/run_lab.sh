#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GO_BIN="${GO_BIN:-}"
if [[ -z "$GO_BIN" ]]; then
  GO_BIN="$(command -v go || true)"
fi
if [[ -z "$GO_BIN" || ! -x "$GO_BIN" ]]; then
  echo "Go toolchain not found. Install Go or set GO_BIN to a Go executable." >&2
  exit 1
fi
export PATH="$(dirname "$GO_BIN"):$PATH"
cd "$ROOT"
rm -rf bin reports
mkdir -p bin reports

cleanup() {
  if [[ -n "${DEMO_PID:-}" ]] && kill -0 "$DEMO_PID" 2>/dev/null; then kill "$DEMO_PID" 2>/dev/null || true; wait "$DEMO_PID" 2>/dev/null || true; fi
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then kill "$API_PID" 2>/dev/null || true; wait "$API_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT

wait_http() {
  local url="$1"
  python3 - "$url" <<'PYWAIT'
import sys, time, urllib.request
url = sys.argv[1]
for _ in range(50):
    try:
        with urllib.request.urlopen(url, timeout=0.2) as response:
            if 200 <= response.status < 500:
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
  "$GO_BIN" version
  "$GO_BIN" env GOOS GOARCH GOVERSION

  echo "== format =="
  "$GO_BIN" fmt ./...

  echo "== tests =="
  "$GO_BIN" test ./...

  echo "== build =="
  "$GO_BIN" build -buildvcs=false -o bin/healthmon ./cmd/healthmon

  echo "== start demo target server =="
  ./bin/healthmon demo -addr 127.0.0.1:18191 > reports/demo-server.log 2>&1 &
  DEMO_PID=$!
  wait_http http://127.0.0.1:18191/ok

  echo "== CLI check =="
  ./bin/healthmon check -config sample_config/targets.json -workers 3 -timeout 900ms -json reports/results.json -csv reports/results.csv
  python3 -m json.tool reports/results.json | sed -n '1,80p'
  echo "-- csv --"
  sed -n '1,10p' reports/results.csv

  echo "== start monitor API =="
  ./bin/healthmon serve -addr 127.0.0.1:18190 -config sample_config/targets.json -workers 3 -timeout 900ms > reports/api-server.log 2>&1 &
  API_PID=$!
  wait_http http://127.0.0.1:18190/health

  echo "== API smoke =="
  python3 - <<'PYSMOKE'
import json, urllib.request
for url in ["http://127.0.0.1:18190/health", "http://127.0.0.1:18190/api/checks"]:
    with urllib.request.urlopen(url, timeout=2) as response:
        body = response.read().decode()
        print(url, response.status)
        print(json.dumps(json.loads(body), ensure_ascii=False, indent=2)[:1200])
PYSMOKE

  echo "== done =="
} | tee reports/transcript.txt
