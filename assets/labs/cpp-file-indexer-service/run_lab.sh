#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf build reports
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
  g++ --version | head -n 1
  cmake --version | head -n 1
  ninja --version

  echo "== configure =="
  cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug

  echo "== build =="
  cmake --build build

  echo "== tests =="
  ctest --test-dir build --output-on-failure

  echo "== CLI scan =="
  ./build/file-indexer --config sample_config/indexer.json --log reports/file-indexer.log scan --json reports/index.json --csv reports/index.csv
  python3 -m json.tool reports/index.json | sed -n '1,120p'
  echo "-- csv --"
  sed -n '1,12p' reports/index.csv
  echo "-- log --"
  sed -n '1,12p' reports/file-indexer.log

  echo "== start local API =="
  ./build/file-indexer --config sample_config/indexer.json --log reports/file-indexer-api.log serve --host 127.0.0.1 --port 18280 > reports/api-server.stdout 2> reports/api-server.stderr &
  API_PID=$!
  wait_http http://127.0.0.1:18280/health

  echo "== API smoke =="
  python3 - <<'PYSMOKE'
import json, urllib.request
for url in ["http://127.0.0.1:18280/health", "http://127.0.0.1:18280/api/summary", "http://127.0.0.1:18280/api/files"]:
    with urllib.request.urlopen(url, timeout=2) as response:
        body = response.read().decode()
        print(url, response.status)
        print(json.dumps(json.loads(body), ensure_ascii=False, indent=2)[:1200])
PYSMOKE

  echo "== help =="
  ./build/file-indexer --help | sed -n '1,80p'

  echo "== done =="
} | tee reports/transcript.txt
