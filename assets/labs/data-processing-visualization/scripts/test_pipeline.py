#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import pipeline


class PipelineTest(unittest.TestCase):
    def test_pipeline_outputs_expected_summary_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = pipeline.run_pipeline(root)
            self.assertEqual(summary["raw_rows"], 20)
            self.assertEqual(summary["clean_rows"], 16)
            self.assertEqual(summary["rejected_rows"], 4)
            self.assertEqual(summary["total_units"], 154)
            self.assertAlmostEqual(summary["total_revenue"], 736.30, places=2)
            self.assertEqual(summary["by_region"][0], {"region": "East", "revenue": 202.25})
            self.assertEqual(summary["by_product"][0], {"product": "Backpack", "revenue": 335.25})

            clean_path = root / "data" / "processed" / "clean_sales.csv"
            reject_path = root / "data" / "processed" / "rejected_sales.csv"
            summary_path = root / "reports" / "summary.json"
            svg_path = root / "reports" / "region_revenue.svg"
            report_path = root / "reports" / "report.md"
            for path in [clean_path, reject_path, summary_path, svg_path, report_path]:
                self.assertTrue(path.exists(), f"missing {path}")

            with reject_path.open(newline="", encoding="utf-8") as f:
                reasons = [row["reason"] for row in csv.DictReader(f)]
            self.assertEqual(reasons, ["missing_region", "invalid_units", "invalid_date", "duplicate_order_id"])

            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["by_month"][1], {"month": "2026-02", "revenue": 301.25})

            with sqlite3.connect(root / "data" / "processed" / "sales.sqlite3") as conn:
                count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
                self.assertEqual(count, 16)

            svg = svg_path.read_text(encoding="utf-8")
            self.assertIn("Revenue by region", svg)
            self.assertIn("East", svg)


if __name__ == "__main__":
    unittest.main()
