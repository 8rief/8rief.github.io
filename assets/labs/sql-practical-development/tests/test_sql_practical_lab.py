from __future__ import annotations

import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.sql_practical_lab import (
    add_ticket,
    connect,
    explain_priority_query,
    export_reports,
    import_tickets_csv,
    migrate,
    run_named_query,
    seed,
    transaction_rollback_demo,
    update_ticket_status,
)


class SqlPracticalLabTest(unittest.TestCase):
    def open_seeded(self, tmp: Path):
        conn = connect(tmp / "lab.db")
        migrate(conn)
        seed(conn)
        return conn

    def test_seed_and_report_queries(self):
        with tempfile.TemporaryDirectory() as d:
            with self.open_seeded(Path(d)) as conn:
                open_rows = run_named_query(conn, "open_tickets")
                self.assertEqual(len(open_rows), 4)
                self.assertEqual(open_rows[0]["priority"], 5)
                project_rows = run_named_query(conn, "project_summary")
                self.assertEqual({row["project"] for row in project_rows}, {"blog-platform", "lab-runner", "research-notes"})

    def test_parameterized_insert_preserves_quotes(self):
        with tempfile.TemporaryDirectory() as d:
            with self.open_seeded(Path(d)) as conn:
                ticket_id = add_ticket(
                    conn,
                    project="blog-platform",
                    title="Reader's SQL note; no string concat",
                    priority=2,
                    assignee="Alice",
                )
                row = conn.execute("SELECT title FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
                self.assertEqual(row["title"], "Reader's SQL note; no string concat")

    def test_status_update_records_event(self):
        with tempfile.TemporaryDirectory() as d:
            with self.open_seeded(Path(d)) as conn:
                update_ticket_status(conn, 2, "done")
                status = conn.execute("SELECT status FROM tickets WHERE id = ?", (2,)).fetchone()["status"]
                self.assertEqual(status, "done")
                event_count = conn.execute(
                    "SELECT COUNT(*) AS n FROM ticket_events WHERE ticket_id = ? AND event_type = 'status'",
                    (2,),
                ).fetchone()["n"]
                self.assertEqual(event_count, 1)

    def test_transaction_rolls_back_on_foreign_key_failure(self):
        with tempfile.TemporaryDirectory() as d:
            with self.open_seeded(Path(d)) as conn:
                result = transaction_rollback_demo(conn)
                self.assertTrue(result["rolled_back"])
                self.assertEqual(result["before"], result["after"])

    def test_import_csv_and_exports(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            csv_path = root / "new.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["project", "title", "priority", "assignee"])
                writer.writeheader()
                writer.writerow({"project": "lab-runner", "title": "Imported report", "priority": "3", "assignee": "Bo"})
            with self.open_seeded(root) as conn:
                created = import_tickets_csv(conn, csv_path)
                self.assertEqual(len(created), 1)
                exports = export_reports(conn, root / "reports")
            report = json.loads(exports["json"].read_text(encoding="utf-8"))
            self.assertIn("project_summary", report)
            self.assertTrue(exports["csv"].read_text(encoding="utf-8").startswith("project,id,title"))

    def test_explain_query_plan_uses_ticket_index(self):
        with tempfile.TemporaryDirectory() as d:
            with self.open_seeded(Path(d)) as conn:
                plan = "\n".join(str(row["detail"]) for row in explain_priority_query(conn))
                self.assertIn("tickets", plan)
                self.assertIn("idx_tickets_status_priority", plan)

    def test_constraints_reject_invalid_status(self):
        with tempfile.TemporaryDirectory() as d:
            with self.open_seeded(Path(d)) as conn:
                with self.assertRaises(sqlite3.IntegrityError):
                    with conn:
                        conn.execute(
                            "INSERT INTO tickets(project_id, title, status, priority, estimate_hours, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (1, "bad status", "blocked", 3, 1.0, "2026-06-28T00:00:00Z"),
                        )


if __name__ == "__main__":
    unittest.main()
