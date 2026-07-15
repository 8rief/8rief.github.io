#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf reports
mkdir -p reports
exec > >(tee reports/transcript.txt) 2>&1
export PYTHONPATH="$ROOT/src"
HOST="127.0.0.1"
PORT="18480"
BASE_URL="http://${HOST}:${PORT}"
SERVER_PID=""
cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

printf '== environment ==\n'
python3 --version
uname -srm
command -v curl
command -v ss
command -v getent || true

printf '\n== local resolver observations ==\n'
getent hosts localhost || true
printf 'resolv.conf nameserver lines:\n'
grep -E '^(nameserver|search|options)' /etc/resolv.conf || true

printf '\n== unit tests ==\n'
python3 -m unittest discover -s tests -v

printf '\n== start loopback service ==\n'
python3 -m local_netsec_lab.cli server --host "$HOST" --port "$PORT" --public-dir sample_public --outside-dir outside_area > reports/server.stdout 2> reports/server.stderr &
SERVER_PID=$!
for _ in $(seq 1 60); do
  if curl -fsS "$BASE_URL/health" > reports/health.json 2>/dev/null; then
    break
  fi
  sleep 0.1
done
cat reports/health.json

printf '\n== listening socket with ss ==\n'
ss -ltn | tee reports/ss_listening.txt
if ! grep -q ":${PORT}" reports/ss_listening.txt; then
  echo "expected port ${PORT} not found in ss output" >&2
  exit 1
fi

printf '\n== curl verbose trace ==\n'
curl -v -sS "$BASE_URL/health" -o reports/health_body.json 2> reports/curl_health_verbose.txt
cat reports/curl_health_verbose.txt

printf '\n== response headers ==\n'
curl -sS -D reports/headers.txt -o reports/health_body_2.json "$BASE_URL/health"
cat reports/headers.txt

printf '\n== local-only service map ==\n'
python3 -m local_netsec_lab.cli map --host "$HOST" --ports "18479-18481" --output reports/service_map.json
cat reports/service_map.json

printf '\n== path boundary evidence ==\n'
python3 -m local_netsec_lab.cli path-boundary --base-url "$BASE_URL" --output reports/path_boundary.json
cat reports/path_boundary.json

printf '\n== command boundary evidence ==\n'
python3 -m local_netsec_lab.cli command-boundary --output reports/command_boundary.json
cat reports/command_boundary.json

printf '\n== hardening report ==\n'
python3 -m local_netsec_lab.cli hardening --base-url "$BASE_URL" --bind-host "$HOST" --output reports/hardening_report.json
cat reports/hardening_report.json

printf '\n== generated artifacts ==\n'
find reports -maxdepth 2 -type f | sort
printf '\n== done ==\n'
