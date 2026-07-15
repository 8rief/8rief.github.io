#!/usr/bin/env python3
"""Run the runtime metrics demo and write a transcript."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime_metrics_demo import aggregate, default_events, evaluate_alerts, read_jsonl, run_pipeline, write_jsonl  # noqa: E402

REPORTS = ROOT / "reports"


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    events_path = REPORTS / "runtime_events.jsonl"
    write_jsonl(events_path, default_events())
    events = read_jsonl(events_path)
    pipeline = run_pipeline(events_path, REPORTS)
    metrics = pipeline["metrics"]
    alerts = pipeline["alerts"]
    small_metrics = aggregate(events[:4])
    small_alerts = evaluate_alerts(small_metrics)
    summary = {
        "jsonl_events_valid": len(events) == 12,
        "request_count": metrics["request_count"],
        "errors_5xx": metrics["errors_5xx"],
        "error_rate": metrics["error_rate"],
        "p90_ms": metrics["latency_ms"]["p90"],
        "slow_rate": metrics["slow_rate"],
        "high_error_rate_alert": any(a["name"] == "high_error_rate" and a["state"] == "firing" for a in alerts),
        "high_p90_latency_alert": any(a["name"] == "high_p90_latency" and a["state"] == "firing" for a in alerts),
        "small_window_suppressed": len(small_alerts) == 1 and small_alerts[0]["name"] == "insufficient_sample",
        "bucket_total_matches": sum(metrics["latency_buckets_ms"].values()) == metrics["request_count"],
        "endpoint_reported": "/api/report" in metrics["endpoint_counts"],
    }
    summary["run_status"] = "ok" if all(
        summary[k]
        for k in [
            "jsonl_events_valid",
            "high_error_rate_alert",
            "high_p90_latency_alert",
            "small_window_suppressed",
            "bucket_total_matches",
            "endpoint_reported",
        ]
    ) else "fail"
    (REPORTS / "metrics_probe.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Runtime metrics probe transcript",
        "",
        f"JSONL_EVENTS_VALID={'yes' if summary['jsonl_events_valid'] else 'no'}",
        f"REQUEST_COUNT={summary['request_count']}",
        f"ERRORS_5XX={summary['errors_5xx']}",
        f"ERROR_RATE={summary['error_rate']:.3f}",
        f"LATENCY_P90_MS={summary['p90_ms']}",
        f"SLOW_RATE={summary['slow_rate']:.3f}",
        f"HIGH_ERROR_RATE_ALERT={'yes' if summary['high_error_rate_alert'] else 'no'}",
        f"HIGH_P90_LATENCY_ALERT={'yes' if summary['high_p90_latency_alert'] else 'no'}",
        f"SMALL_WINDOW_SUPPRESSED={'yes' if summary['small_window_suppressed'] else 'no'}",
        f"BUCKET_TOTAL_MATCHES={'yes' if summary['bucket_total_matches'] else 'no'}",
        f"ENDPOINT_REPORTED={'yes' if summary['endpoint_reported'] else 'no'}",
        f"RUN_STATUS={summary['run_status']}",
    ]
    transcript = "\n".join(lines) + "\n"
    (REPORTS / "transcript.md").write_text(transcript, encoding="utf-8")
    print(transcript)
    return 0 if summary["run_status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
