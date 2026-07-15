#!/usr/bin/env bash
set -euo pipefail

out_dir=${1:?usage: generate_logs.sh OUT_DIR}
mkdir -p "$out_dir"

cat > "$out_dir/app-2026-07-01.log" <<'LOG'
ts=2026-07-01T08:00:01Z service=api level=INFO status=200 latency_ms=34 path=/api/orders user=alice
ts=2026-07-01T08:01:11Z service=api level=INFO status=200 latency_ms=45 path=/api/orders user=bob
ts=2026-07-01T08:03:20Z service=auth level=INFO status=200 latency_ms=28 path=/login user=alice
ts=2026-07-01T08:04:05Z service=api level=WARN status=429 latency_ms=120 path=/api/search user=anonymous
ts=2026-07-01T08:06:42Z service=api level=ERROR status=500 latency_ms=240 path=/api/orders user=alice
ts=2026-07-01T08:07:10Z service=worker level=INFO status=200 latency_ms=310 path=/jobs/payment user=system
ts=2026-07-01T08:08:19Z service=worker level=ERROR status=0 latency_ms=830 path=/jobs/payment user=system
ts=2026-07-01T08:09:44Z service=api level=INFO status=201 latency_ms=55 path=/api/orders user=bob
LOG

# The space in this file name is intentional. It makes unsafe whitespace-based loops fail.
cat > "$out_dir/app 2026-07-02.log" <<'LOG'
ts=2026-07-02T09:00:12Z service=api level=INFO status=200 latency_ms=62 path=/api/report user=carol
ts=2026-07-02T09:01:30Z service=api level=ERROR status=503 latency_ms=650 path=/api/report user=carol
ts=2026-07-02T09:02:41Z service=auth level=ERROR status=401 latency_ms=38 path=/login user=mallory
ts=2026-07-02T09:04:55Z service=auth level=INFO status=200 latency_ms=33 path=/login user=bob
ts=2026-07-02T09:05:03Z service=api level=INFO status=200 latency_ms=78 path=/api/search user=dave
ts=2026-07-02T09:07:29Z service=api level=WARN status=429 latency_ms=145 path=/api/search user=anonymous
ts=2026-07-02T09:08:31Z service=api level=ERROR status=500 latency_ms=410 path=/api/orders user=bob
ts=2026-07-02T09:10:00Z service=worker level=INFO status=200 latency_ms=500 path=/jobs/reconcile user=system
LOG
