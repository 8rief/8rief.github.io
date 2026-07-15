#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports data/runtime
# The container runs as a non-root app user. Make the bind-mounted teaching
# runtime directory writable without sudo or host-specific chown.
chmod 0777 data/runtime
TRANSCRIPT="reports/transcript.txt"
IMAGE="container-deployment-practice:local"
CONTAINER="container-deployment-practice-web"
HOST_URL="http://127.0.0.1:18080"
exec > >(tee "$TRANSCRIPT") 2>&1

wait_container_healthy() {
  local name="$1"
  local status=""
  for _ in $(seq 1 20); do
    status="$(docker inspect "$name" --format '{{.State.Health.Status}}' 2>/dev/null || true)"
    if [[ "$status" == "healthy" ]]; then
      echo "container_health=healthy"
      return 0
    fi
    sleep 1
  done
  echo "container_health=${status:-unknown}"
  return 1
}

echo "lab=container-deployment-practice"
echo "pwd=$ROOT"
echo "python_version=$(python3 --version)"
echo "docker_server_version=$(docker version --format '{{.Server.Version}}')"
echo "compose_version=$(docker compose version --short)"

echo
echo "syntax and unit tests"
python3 -m py_compile app/server.py scripts/test_server.py scripts/smoke.py scripts/write_report.py
python3 -m unittest discover -s scripts -p 'test_*.py'

echo
echo "cleanup own lab container"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
rm -f data/runtime/state.json reports/smoke-first.json reports/smoke-after-restart.json reports/summary.json reports/report.md reports/container_deployment_flow.svg reports/docker-info.json

echo
echo "build image"
docker build -t "$IMAGE" .
image_id="$(docker image inspect "$IMAGE" --format '{{.Id}}')"
echo "image_id=$image_id"

echo
echo "run container with loopback port and bind mount"
docker run -d --rm \
  --name "$CONTAINER" \
  -p 127.0.0.1:18080:8080 \
  -e APP_NAME=container-lab \
  -e DATA_DIR=/data \
  -v "$ROOT/data/runtime:/data" \
  "$IMAGE"
wait_container_healthy "$CONTAINER"
python3 scripts/smoke.py --base-url "$HOST_URL" --label first --out reports/smoke-first.json

echo
echo "restart container to verify bind-mounted state"
docker stop "$CONTAINER"
docker run -d --rm \
  --name "$CONTAINER" \
  -p 127.0.0.1:18080:8080 \
  -e APP_NAME=container-lab \
  -e DATA_DIR=/data \
  -v "$ROOT/data/runtime:/data" \
  "$IMAGE"
wait_container_healthy "$CONTAINER"
python3 scripts/smoke.py --base-url "$HOST_URL" --label restart --out reports/smoke-after-restart.json

echo
echo "logs and inspect"
docker logs "$CONTAINER" | tail -20
health_status="$(docker inspect "$CONTAINER" --format '{{.State.Health.Status}}')"
echo "container_health=$health_status"

echo
echo "compose config check"
docker compose config >/tmp/container-deployment-compose-config.txt
compose_config_ok=true
cat > reports/docker-info.json <<JSON
{
  "docker_server_version": "$(docker version --format '{{.Server.Version}}')",
  "compose_version": "$(docker compose version --short)",
  "image_tag": "$IMAGE",
  "container_name": "$CONTAINER",
  "compose_config_ok": $compose_config_ok
}
JSON

python3 scripts/write_report.py

echo
echo "visible result markers"
echo "summary_ready=reports/summary.json"
echo "chart_ready=reports/container_deployment_flow.svg"
echo "report_ready=reports/report.md"
echo "state_ready=data/runtime/state.json"
echo "container_deployment_status=ok"

echo
echo "cleanup running container"
docker stop "$CONTAINER" >/dev/null
