#!/usr/bin/env python3
"""Deterministic JSONL runtime metrics and alert aggregation demo."""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

BUCKET_BOUNDS_MS = [50, 100, 250, 500, 1000]


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class RequestEvent:
    ts: float
    request_id: str
    endpoint: str
    status: int
    latency_ms: float

    @property
    def status_family(self) -> str:
        return f"{self.status // 100}xx"

    @property
    def ok(self) -> bool:
        return self.status < 500

    @property
    def slow(self) -> bool:
        return self.latency_ms > 250

    def to_json(self) -> dict[str, Any]:
        return {
            "event": "request_finished",
            "ts": self.ts,
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "status": self.status,
            "latency_ms": self.latency_ms,
        }


def default_events() -> list[RequestEvent]:
    # 12 events: enough samples to evaluate threshold alerts. Three 5xx errors
    # make error_rate=0.25, and p90 latency is high because the last two
    # requests are slow.
    raw = [
        (0.0, "req-001", "/api/tasks", 200, 42),
        (1.0, "req-002", "/api/tasks", 200, 55),
        (2.0, "req-003", "/api/tasks", 200, 63),
        (3.0, "req-004", "/api/tasks", 201, 70),
        (4.0, "req-005", "/api/tasks", 500, 310),
        (5.0, "req-006", "/api/tasks", 200, 82),
        (6.0, "req-007", "/api/report", 200, 95),
        (7.0, "req-008", "/api/report", 503, 420),
        (8.0, "req-009", "/api/report", 200, 120),
        (9.0, "req-010", "/api/report", 502, 510),
        (10.0, "req-011", "/api/report", 200, 240),
        (11.0, "req-012", "/api/report", 200, 780),
    ]
    return [RequestEvent(*row) for row in raw]


def write_jsonl(path: Path, events: Iterable[RequestEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(canonical_json(event.to_json()) + "\n")


def parse_event(payload: dict[str, Any]) -> RequestEvent:
    required = {"event", "ts", "request_id", "endpoint", "status", "latency_ms"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"missing fields: {','.join(missing)}")
    if payload["event"] != "request_finished":
        raise ValueError(f"unsupported event: {payload['event']!r}")
    status = int(payload["status"])
    latency_ms = float(payload["latency_ms"])
    if not (100 <= status <= 599):
        raise ValueError(f"invalid status: {status}")
    if latency_ms < 0:
        raise ValueError(f"invalid latency_ms: {latency_ms}")
    endpoint = str(payload["endpoint"])
    if not endpoint.startswith("/"):
        raise ValueError(f"invalid endpoint: {endpoint!r}")
    request_id = str(payload["request_id"])
    if not request_id:
        raise ValueError("empty request_id")
    return RequestEvent(
        ts=float(payload["ts"]),
        request_id=request_id,
        endpoint=endpoint,
        status=status,
        latency_ms=latency_ms,
    )


def read_jsonl(path: Path) -> list[RequestEvent]:
    events: list[RequestEvent] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            events.append(parse_event(payload))
        except Exception as exc:  # raise with line context at file boundary
            raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return events


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (pct / 100) * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return float(ordered[int(rank)])
    weight = rank - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def latency_buckets(latencies: Iterable[float]) -> dict[str, int]:
    counts: dict[str, int] = {f"le_{bound}ms": 0 for bound in BUCKET_BOUNDS_MS}
    counts["gt_1000ms"] = 0
    for latency in latencies:
        placed = False
        for bound in BUCKET_BOUNDS_MS:
            if latency <= bound:
                counts[f"le_{bound}ms"] += 1
                placed = True
                break
        if not placed:
            counts["gt_1000ms"] += 1
    return counts


def aggregate(events: list[RequestEvent], slow_threshold_ms: float = 250.0) -> dict[str, Any]:
    latencies = [e.latency_ms for e in events]
    request_count = len(events)
    status_families = Counter(e.status_family for e in events)
    endpoint_counts = Counter(e.endpoint for e in events)
    endpoint_errors: dict[str, int] = defaultdict(int)
    endpoint_latencies: dict[str, list[float]] = defaultdict(list)
    for event in events:
        endpoint_latencies[event.endpoint].append(event.latency_ms)
        if event.status >= 500:
            endpoint_errors[event.endpoint] += 1
    errors_5xx = sum(1 for e in events if e.status >= 500)
    slow_requests = sum(1 for e in events if e.latency_ms > slow_threshold_ms)
    metrics = {
        "window": {
            "start_ts": min((e.ts for e in events), default=None),
            "end_ts": max((e.ts for e in events), default=None),
        },
        "request_count": request_count,
        "status_family_counts": dict(sorted(status_families.items())),
        "endpoint_counts": dict(sorted(endpoint_counts.items())),
        "endpoint_error_counts": dict(sorted(endpoint_errors.items())),
        "latency_buckets_ms": latency_buckets(latencies),
        "latency_ms": {
            "min": min(latencies) if latencies else 0.0,
            "p50": round(percentile(latencies, 50), 3),
            "p90": round(percentile(latencies, 90), 3),
            "max": max(latencies) if latencies else 0.0,
        },
        "errors_5xx": errors_5xx,
        "slow_requests": slow_requests,
        "error_rate": round(errors_5xx / request_count, 6) if request_count else 0.0,
        "slow_rate": round(slow_requests / request_count, 6) if request_count else 0.0,
        "slow_threshold_ms": slow_threshold_ms,
    }
    metrics["endpoint_latency_p90_ms"] = {
        endpoint: round(percentile(values, 90), 3) for endpoint, values in sorted(endpoint_latencies.items())
    }
    return metrics


def evaluate_alerts(
    metrics: dict[str, Any],
    *,
    min_requests: int = 10,
    max_error_rate: float = 0.20,
    max_p90_ms: float = 300.0,
) -> list[dict[str, Any]]:
    count = int(metrics["request_count"])
    alerts: list[dict[str, Any]] = []
    if count < min_requests:
        return [
            {
                "name": "insufficient_sample",
                "severity": "info",
                "observed": count,
                "threshold": min_requests,
                "state": "suppressed",
                "reason": "not enough requests to evaluate rate/latency thresholds",
            }
        ]
    error_rate = float(metrics["error_rate"])
    p90 = float(metrics["latency_ms"]["p90"])
    if error_rate > max_error_rate:
        alerts.append(
            {
                "name": "high_error_rate",
                "severity": "page",
                "observed": error_rate,
                "threshold": max_error_rate,
                "sample_count": count,
                "state": "firing",
            }
        )
    if p90 > max_p90_ms:
        alerts.append(
            {
                "name": "high_p90_latency",
                "severity": "ticket",
                "observed": p90,
                "threshold": max_p90_ms,
                "sample_count": count,
                "state": "firing",
            }
        )
    return alerts


def write_reports(metrics: dict[str, Any], alerts: list[dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "alerts.json").write_text(json.dumps(alerts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Runtime metrics report",
        "",
        "| Metric | Value | Meaning |",
        "| --- | ---: | --- |",
        f"| request_count | {metrics['request_count']} | number of request_finished events in the window |",
        f"| errors_5xx | {metrics['errors_5xx']} | server-side failures |",
        f"| error_rate | {metrics['error_rate']:.3f} | errors_5xx / request_count |",
        f"| latency_p50_ms | {metrics['latency_ms']['p50']} | median observed latency |",
        f"| latency_p90_ms | {metrics['latency_ms']['p90']} | high-tail observed latency |",
        f"| slow_rate | {metrics['slow_rate']:.3f} | fraction above {metrics['slow_threshold_ms']} ms |",
        "",
        "## Alerts",
        "",
    ]
    if alerts:
        lines.extend(["| Alert | State | Observed | Threshold |", "| --- | --- | ---: | ---: |"])
        for alert in alerts:
            lines.append(f"| {alert['name']} | {alert['state']} | {alert['observed']} | {alert['threshold']} |")
    else:
        lines.append("No alerts fired for this window.")
    lines.extend([
        "",
        "## Boundary",
        "",
        "Logs answer what happened to one request. Metrics answer what happened in the window. Alerts answer whether a rule needs attention.",
    ])
    (out_dir / "runtime_metrics_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pipeline(events_path: Path, out_dir: Path) -> dict[str, Any]:
    events = read_jsonl(events_path)
    metrics = aggregate(events)
    alerts = evaluate_alerts(metrics)
    write_reports(metrics, alerts, out_dir)
    return {"metrics": metrics, "alerts": alerts}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aggregate JSONL runtime events into metrics and alerts.")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate-events", help="write deterministic JSONL request events")
    gen.add_argument("--output", required=True)
    agg = sub.add_parser("aggregate", help="aggregate an event JSONL file")
    agg.add_argument("--events", required=True)
    agg.add_argument("--out-dir", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "generate-events":
        write_jsonl(Path(args.output), default_events())
        return 0
    if args.command == "aggregate":
        run_pipeline(Path(args.events), Path(args.out_dir))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
