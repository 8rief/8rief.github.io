import json
import tempfile
import unittest
from pathlib import Path

from test_pyramid_demo import compare_golden, run_pipeline

ROOT = Path(__file__).resolve().parents[1]


class IntegrationPipelineTests(unittest.TestCase):
    def test_pipeline_writes_summary_and_jsonl_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "summary.json"
            log = Path(tmp) / "events.jsonl"
            summary = run_pipeline(ROOT / "data" / "orders.csv", out, log)
            self.assertEqual(summary["net_cents"], 14265)
            self.assertEqual(summary["top_customer"], "bob")
            self.assertEqual(json.loads(out.read_text())["line_count"], 4)
            events = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([event["event"] for event in events], ["start", "loaded", "summary_written"])

    def test_golden_fixture_matches_current_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "summary.json"
            log = Path(tmp) / "events.jsonl"
            run_pipeline(ROOT / "data" / "orders.csv", out, log)
            ok, diffs = compare_golden(out, ROOT / "fixtures" / "golden_summary.json")
            self.assertTrue(ok, diffs)


if __name__ == "__main__":
    unittest.main()
