from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from migration_demo import (
    MIGRATIONS,
    MigrationError,
    applied_migrations,
    connect,
    current_version,
    dump_schema,
    index_names,
    migrate_to,
    migration_report,
    rollback_to,
    seed_users,
    user_version,
)

ROOT = Path(__file__).resolve().parents[1]


class MigrationDemoTests(unittest.TestCase):
    def test_migrate_to_latest_is_idempotent_and_old_query_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect(Path(tmp) / "app.db")
            try:
                self.assertEqual(migrate_to(conn, target=1), [1])
                seed_users(conn, ROOT / "fixtures" / "users_v1.csv")
                self.assertEqual(migrate_to(conn), [2, 3])
                self.assertEqual(migrate_to(conn), [])
                report = migration_report(conn)
                self.assertEqual(report["schema_version"], 3)
                self.assertEqual(report["user_version"], 3)
                self.assertEqual(report["users"], 3)
                self.assertEqual(report["display_name_backfilled"], 3)
                self.assertTrue(report["normalized_emails_valid"])
                self.assertTrue(report["old_query_compatible"])
                self.assertIn("idx_users_email_normalized", index_names(conn))
            finally:
                conn.close()

    def test_duplicate_preflight_aborts_version_3_without_corrupting_version_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect(Path(tmp) / "bad.db")
            try:
                migrate_to(conn, target=1)
                seed_users(conn, ROOT / "fixtures" / "users_duplicate_email.csv")
                migrate_to(conn, target=2)
                with self.assertRaises(MigrationError):
                    migrate_to(conn, target=3)
                self.assertEqual(current_version(conn), 2)
                self.assertEqual(user_version(conn), 2)
                self.assertNotIn("idx_users_email_normalized", index_names(conn))
                versions = sorted(applied_migrations(conn))
                self.assertEqual(versions, [1, 2])
            finally:
                conn.close()

    def test_rollback_to_version_2_removes_normalized_email_but_keeps_display_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect(Path(tmp) / "rollback.db")
            try:
                migrate_to(conn, target=1)
                seed_users(conn, ROOT / "fixtures" / "users_v1.csv")
                migrate_to(conn)
                self.assertEqual(rollback_to(conn, 2), [3])
                report = migration_report(conn)
                self.assertEqual(report["schema_version"], 2)
                self.assertEqual(report["user_version"], 2)
                self.assertIn("display_name", report["columns"])
                self.assertNotIn("email_normalized", report["columns"])
                self.assertEqual(report["display_name_backfilled"], 3)
            finally:
                conn.close()

    def test_checksum_mismatch_stops_future_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect(Path(tmp) / "checksum.db")
            try:
                migrate_to(conn, target=1)
                conn.execute("UPDATE schema_migrations SET checksum='bad' WHERE version=1")
                conn.commit()
                with self.assertRaises(MigrationError):
                    migrate_to(conn)
            finally:
                conn.close()

    def test_dump_schema_contains_migration_table_and_unique_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect(Path(tmp) / "schema.db")
            try:
                migrate_to(conn, target=1)
                seed_users(conn, ROOT / "fixtures" / "users_v1.csv")
                migrate_to(conn)
                schema = dump_schema(conn)
                self.assertIn("CREATE TABLE schema_migrations", schema)
                self.assertIn("CREATE UNIQUE INDEX idx_users_email_normalized", schema)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
