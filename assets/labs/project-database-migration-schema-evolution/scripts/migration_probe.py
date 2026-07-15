#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from migration_demo import MigrationError, connect, dump_schema, migrate_to, migration_report, rollback_to, seed_users

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def yes(value: bool) -> str:
    return "yes" if value else "no"


def run_happy_path() -> dict[str, Any]:
    db = REPORTS / "app.db"
    if db.exists():
        db.unlink()
    conn = connect(db)
    try:
        applied_first = migrate_to(conn, target=1)
        seeded = seed_users(conn, ROOT / "fixtures" / "users_v1.csv")
        applied_rest = migrate_to(conn)
        reapplied = migrate_to(conn)
        report = migration_report(conn)
        schema = dump_schema(conn)
        (REPORTS / "schema_after_v3.sql").write_text(schema, encoding="utf-8")
        report.update({
            "db_path": "reports/app.db",
            "seeded": seeded,
            "applied_first": applied_first,
            "applied_rest": applied_rest,
            "reapply_noop": reapplied == [],
            "unique_index_present": "idx_users_email_normalized" in report["index_names"],
        })
        return report
    finally:
        conn.close()


def run_rollback_probe() -> dict[str, Any]:
    db = REPORTS / "rollback.db"
    if db.exists():
        db.unlink()
    conn = connect(db)
    try:
        migrate_to(conn, target=1)
        seed_users(conn, ROOT / "fixtures" / "users_v1.csv")
        migrate_to(conn)
        rolled = rollback_to(conn, 2)
        report = migration_report(conn)
        report.update({
            "rolled_back": rolled,
            "email_normalized_removed": "email_normalized" not in report["columns"],
            "display_name_kept": "display_name" in report["columns"],
            "unique_index_removed": "idx_users_email_normalized" not in report["index_names"],
        })
        return report
    finally:
        conn.close()


def run_duplicate_probe() -> dict[str, Any]:
    db = REPORTS / "duplicate.db"
    if db.exists():
        db.unlink()
    conn = connect(db)
    try:
        migrate_to(conn, target=1)
        seed_users(conn, ROOT / "fixtures" / "users_duplicate_email.csv")
        migrate_to(conn, target=2)
        try:
            migrate_to(conn, target=3)
        except MigrationError as exc:
            failure = str(exc)
        else:
            failure = ""
        report = migration_report(conn)
        report.update({
            "duplicate_preflight_failed": bool(failure),
            "duplicate_failure_message": failure,
            "stayed_at_version_2": report["schema_version"] == 2,
            "migration_003_absent": all(row["version"] != 3 for row in report["applied_migrations"]),
        })
        return report
    finally:
        conn.close()


def render_report(summary: dict[str, Any]) -> str:
    latest = summary["latest"]
    rollback = summary["rollback"]
    duplicate = summary["duplicate"]
    return f"""# Database migration probe report

| Check | Result |
| --- | --- |
| latest schema version | {latest['schema_version']} |
| PRAGMA user_version | {latest['user_version']} |
| migrations applied | {len(latest['applied_migrations'])} |
| users | {latest['users']} |
| display names backfilled | {latest['display_name_backfilled']} |
| normalized emails valid | {yes(latest['normalized_emails_valid'])} |
| unique index present | {yes(latest['unique_index_present'])} |
| old query compatible | {yes(latest['old_query_compatible'])} |
| reapply no-op | {yes(latest['reapply_noop'])} |
| rollback removed email_normalized | {yes(rollback['email_normalized_removed'])} |
| rollback kept display_name | {yes(rollback['display_name_kept'])} |
| duplicate preflight failed | {yes(duplicate['duplicate_preflight_failed'])} |
| duplicate stayed at v2 | {yes(duplicate['stayed_at_version_2'])} |

The probe demonstrates expand/backfill/constraint migration phases, rollback to a previous schema version, and a failed migration that leaves earlier committed migrations intact.
"""


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    latest = run_happy_path()
    rollback = run_rollback_probe()
    duplicate = run_duplicate_probe()
    summary = {"latest": latest, "rollback": rollback, "duplicate": duplicate}
    (REPORTS / "migration_probe.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (REPORTS / "migration_report.md").write_text(render_report(summary), encoding="utf-8")

    print("SCHEMA_VERSION=%s" % latest["schema_version"])
    print("USER_VERSION=%s" % latest["user_version"])
    print("MIGRATIONS_APPLIED=%s" % len(latest["applied_migrations"]))
    print("USERS=%s" % latest["users"])
    print("DISPLAY_NAME_BACKFILLED=%s" % latest["display_name_backfilled"])
    print("NORMALIZED_EMAILS_VALID=%s" % yes(latest["normalized_emails_valid"]))
    print("UNIQUE_INDEX_PRESENT=%s" % yes(latest["unique_index_present"]))
    print("OLD_QUERY_COMPATIBLE=%s" % yes(latest["old_query_compatible"]))
    print("REAPPLY_NOOP=%s" % yes(latest["reapply_noop"]))
    print("ROLLBACK_TO_2_REMOVED_EMAIL_NORMALIZED=%s" % yes(rollback["email_normalized_removed"]))
    print("ROLLBACK_TO_2_KEPT_DISPLAY_NAME=%s" % yes(rollback["display_name_kept"]))
    print("ROLLBACK_TO_2_REMOVED_UNIQUE_INDEX=%s" % yes(rollback["unique_index_removed"]))
    print("DUPLICATE_PREFLIGHT_FAILED=%s" % yes(duplicate["duplicate_preflight_failed"]))
    print("DUPLICATE_STAYED_AT_VERSION_2=%s" % yes(duplicate["stayed_at_version_2"]))
    print("MIGRATION_003_ABSENT_AFTER_FAILURE=%s" % yes(duplicate["migration_003_absent"]))
    print("RUN_STATUS=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
