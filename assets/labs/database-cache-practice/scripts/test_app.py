#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import app


class DatabaseCachePracticeTest(unittest.TestCase):
    def test_demo_outputs_expected_database_and_cache_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = app.run_demo(root)
            summary = payload["summary"]
            self.assertEqual(summary["schema_version"], 2)
            self.assertEqual(summary["product_count"], 5)
            self.assertEqual(summary["order_count"], 2)
            self.assertEqual(summary["total_revenue_cents"], 17790)
            self.assertEqual(summary["total_stock"], 158)
            self.assertTrue(payload["query_plan_uses_index"])
            self.assertEqual(payload["cache_stats"], {"hits": 1, "misses": 3, "invalidations": 1, "expirations": 1})

            report = payload["category_report"]
            self.assertEqual(report[0], {"category": "bags", "stock_left": 16, "units_sold": 2, "revenue_cents": 9198})
            self.assertEqual(report[1]["category"], "stationery")
            self.assertEqual(report[1]["revenue_cents"], 6693)

            for path in ["reports/summary.json", "reports/report.md", "reports/category_revenue.svg", "data/app.sqlite3"]:
                self.assertTrue((root / path).exists(), path)

            saved = json.loads((root / "reports" / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["summary"]["total_revenue_cents"], 17790)
            self.assertTrue(saved["query_plan_uses_index"])

            with sqlite3.connect(root / "data" / "app.sqlite3") as conn:
                conn.row_factory = sqlite3.Row
                stock = conn.execute("SELECT stock FROM products WHERE sku = ?", ("BK-200",)).fetchone()["stock"]
                self.assertEqual(stock, 16)
                order_items = conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
                self.assertEqual(order_items, 4)


if __name__ == "__main__":
    unittest.main()
