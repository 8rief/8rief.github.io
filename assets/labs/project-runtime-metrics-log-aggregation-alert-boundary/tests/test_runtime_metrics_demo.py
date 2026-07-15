#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from runtime_metrics_demo import (  # noqa: E402
    aggregate,
    default_events,
    evaluate_alerts,
    read_jsonl,
    run_pipeline,
    write_jsonl,
)


class RuntimeMetricsTests(unittest.TestCase):
    def test_aggregate_counters_rates_and_buckets(self):
        metrics = aggregate(default_events())
        self.assertEqual(metrics["request_count"], 12)
        self.assertEqual(metrics["errors_5xx"], 3)
        self.assertAlmostEqual(metrics["error_rate"], 0.25)
        self.assertEqual(sum(metrics["latency_buckets_ms"].values()), 12)
        self.assertEqual(metrics["status_family_counts"], {"2xx": 9, "5xx": 3})
        self.assertEqual(metrics["endpoint_counts"]["/api/report"], 6)
        self.assertGreater(metrics["latency_ms"]["p90"], 300)

    def test_alerts_fire_with_enough_samples(self):
        alerts = evaluate_alerts(aggregate(default_events()))
        names = {alert["name"] for alert in alerts if alert["state"] == "firing"}
        self.assertIn("high_error_rate", names)
        self.assertIn("high_p90_latency", names)

    def test_small_sample_suppresses_threshold_alerts(self):
        alerts = evaluate_alerts(aggregate(default_events()[:4]))
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["name"], "insufficient_sample")
        self.assertEqual(alerts[0]["state"], "suppressed")

    def test_jsonl_round_trip_and_reports(self):
        with tempfile.TemporaryDirectory(prefix="metrics-demo-") as tmp:
            root = Path(tmp)
            events_path = root / "events.jsonl"
            out_dir = root / "reports"
            write_jsonl(events_path, default_events())
            events = read_jsonl(events_path)
            self.assertEqual(len(events), 12)
            result = run_pipeline(events_path, out_dir)
            self.assertTrue((out_dir / "metrics.json").exists())
            self.assertTrue((out_dir / "alerts.json").exists())
            self.assertTrue((out_dir / "runtime_metrics_report.md").exists())
            saved = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["request_count"], result["metrics"]["request_count"])

    def test_malformed_event_reports_line_number(self):
        with tempfile.TemporaryDirectory(prefix="metrics-bad-") as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text('{"event":"request_finished","status":700}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r":1:"):
                read_jsonl(path)


if __name__ == "__main__":
    unittest.main()
