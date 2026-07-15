#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    statement_id: str
    up: Callable[[sqlite3.Connection], None]
    down: Callable[[sqlite3.Connection], None] | None = None

    @property
    def checksum(self) -> str:
        return hashlib.sha256(f"{self.version}:{self.name}:{self.statement_id}".encode("utf-8")).hexdigest()


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def migration_001_up(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            full_name TEXT NOT NULL
        )
        """
    )
    conn.execute("PRAGMA user_version = 1")


def migration_001_down(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("PRAGMA user_version = 0")


def migration_002_up(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
    conn.execute("UPDATE users SET display_name = full_name WHERE display_name IS NULL")
    conn.execute("PRAGMA user_version = 2")


def migration_002_down(conn: sqlite3.Connection) -> None:
    rebuild_users_without_columns(conn, keep_columns=["id", "email", "full_name"])
    conn.execute("PRAGMA user_version = 1")


def duplicate_normalized_emails(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT lower(trim(email)) AS email_normalized, count(*) AS count
        FROM users
        GROUP BY lower(trim(email))
        HAVING count(*) > 1
        ORDER BY email_normalized
        """
    ).fetchall()
    return [dict(row) for row in rows]


def migration_003_up(conn: sqlite3.Connection) -> None:
    duplicates = duplicate_normalized_emails(conn)
    if duplicates:
        raise MigrationError("duplicate normalized emails: " + json.dumps(duplicates, sort_keys=True))
    conn.execute("ALTER TABLE users ADD COLUMN email_normalized TEXT")
    conn.execute("UPDATE users SET email_normalized = lower(trim(email))")
    missing = conn.execute("SELECT count(*) FROM users WHERE email_normalized IS NULL OR email_normalized = ''").fetchone()[0]
    if missing:
        raise MigrationError("email_normalized backfill produced empty values")
    conn.execute("CREATE UNIQUE INDEX idx_users_email_normalized ON users(email_normalized)")
    conn.execute("PRAGMA user_version = 3")


def migration_003_down(conn: sqlite3.Connection) -> None:
    conn.execute("DROP INDEX IF EXISTS idx_users_email_normalized")
    rebuild_users_without_columns(conn, keep_columns=["id", "email", "full_name", "display_name"])
    conn.execute("PRAGMA user_version = 2")


def rebuild_users_without_columns(conn: sqlite3.Connection, keep_columns: list[str]) -> None:
    known = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    missing = [col for col in keep_columns if col not in known]
    if missing:
        raise MigrationError("cannot rebuild users; missing columns " + ",".join(missing))
    definitions = {
        "id": "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "email": "email TEXT NOT NULL",
        "full_name": "full_name TEXT NOT NULL",
        "display_name": "display_name TEXT",
        "email_normalized": "email_normalized TEXT",
    }
    select_cols = ", ".join(keep_columns)
    create_cols = ", ".join(definitions[col] for col in keep_columns)
    conn.execute("ALTER TABLE users RENAME TO users_old")
    conn.execute(f"CREATE TABLE users ({create_cols})")
    conn.execute(f"INSERT INTO users ({select_cols}) SELECT {select_cols} FROM users_old")
    conn.execute("DROP TABLE users_old")


MIGRATIONS = [
    Migration(1, "create users v1", "create-users-v1-email-full-name", migration_001_up, migration_001_down),
    Migration(2, "expand users with display_name", "alter-users-add-display-name-backfill", migration_002_up, migration_002_down),
    Migration(3, "backfill normalized email and add unique index", "alter-users-add-normalized-email-unique-index", migration_003_up, migration_003_down),
]


def applied_migrations(conn: sqlite3.Connection) -> dict[int, sqlite3.Row]:
    ensure_migration_table(conn)
    return {row["version"]: row for row in conn.execute("SELECT version, name, checksum, applied_at FROM schema_migrations ORDER BY version")}


def verify_applied_checksums(conn: sqlite3.Connection) -> None:
    applied = applied_migrations(conn)
    expected = {m.version: m for m in MIGRATIONS}
    for version, row in applied.items():
        if version not in expected:
            raise MigrationError(f"unknown applied migration {version}")
        if row["checksum"] != expected[version].checksum:
            raise MigrationError(f"checksum mismatch for migration {version}")


def current_version(conn: sqlite3.Connection) -> int:
    ensure_migration_table(conn)
    row = conn.execute("SELECT coalesce(max(version), 0) FROM schema_migrations").fetchone()
    return int(row[0])


def user_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def migrate_to(conn: sqlite3.Connection, target: int | None = None) -> list[int]:
    ensure_migration_table(conn)
    verify_applied_checksums(conn)
    target_version = target if target is not None else MIGRATIONS[-1].version
    applied_versions: list[int] = []
    for migration in MIGRATIONS:
        if migration.version > target_version:
            break
        if migration.version in applied_migrations(conn):
            continue
        run_transaction(conn, lambda m=migration: apply_one(conn, m))
        applied_versions.append(migration.version)
    return applied_versions


def rollback_to(conn: sqlite3.Connection, target: int) -> list[int]:
    ensure_migration_table(conn)
    verify_applied_checksums(conn)
    rolled_back: list[int] = []
    for migration in sorted(MIGRATIONS, key=lambda m: m.version, reverse=True):
        if migration.version <= target:
            continue
        if migration.version not in applied_migrations(conn):
            continue
        if migration.down is None:
            raise MigrationError(f"migration {migration.version} has no down migration")
        run_transaction(conn, lambda m=migration: rollback_one(conn, m))
        rolled_back.append(migration.version)
    return rolled_back


def run_transaction(conn: sqlite3.Connection, func: Callable[[], None]) -> None:
    try:
        conn.execute("BEGIN")
        func()
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def apply_one(conn: sqlite3.Connection, migration: Migration) -> None:
    migration.up(conn)
    conn.execute(
        "INSERT INTO schema_migrations(version, name, checksum) VALUES (?, ?, ?)",
        (migration.version, migration.name, migration.checksum),
    )


def rollback_one(conn: sqlite3.Connection, migration: Migration) -> None:
    assert migration.down is not None
    migration.down(conn)
    conn.execute("DELETE FROM schema_migrations WHERE version = ?", (migration.version,))


def seed_users(conn: sqlite3.Connection, csv_path: Path) -> int:
    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    with conn:
        conn.executemany(
            "INSERT INTO users(email, full_name) VALUES (?, ?)",
            [(row["email"], row["full_name"]) for row in rows],
        )
    return len(rows)


def schema_columns(conn: sqlite3.Connection) -> list[str]:
    return [row["name"] for row in conn.execute("PRAGMA table_info(users)")]


def index_names(conn: sqlite3.Connection) -> list[str]:
    return [row["name"] for row in conn.execute("PRAGMA index_list(users)")]


def old_query_compatible(conn: sqlite3.Connection) -> bool:
    rows = conn.execute("SELECT id, email, full_name FROM users ORDER BY id").fetchall()
    return len(rows) > 0 and set(rows[0].keys()) == {"id", "email", "full_name"}


def migration_report(conn: sqlite3.Connection) -> dict[str, Any]:
    columns = schema_columns(conn) if table_exists(conn, "users") else []
    users = conn.execute("SELECT count(*) FROM users").fetchone()[0] if table_exists(conn, "users") else 0
    display_backfilled = 0
    normalized_valid = False
    if "display_name" in columns:
        display_backfilled = conn.execute("SELECT count(*) FROM users WHERE display_name IS NOT NULL AND display_name != ''").fetchone()[0]
    if "email_normalized" in columns:
        normalized_valid = conn.execute("SELECT count(*) FROM users WHERE email_normalized = lower(trim(email))").fetchone()[0] == users
    return {
        "schema_version": current_version(conn),
        "user_version": user_version(conn),
        "applied_migrations": [dict(row) for row in conn.execute("SELECT version, name, checksum FROM schema_migrations ORDER BY version")],
        "columns": columns,
        "index_names": index_names(conn) if table_exists(conn, "users") else [],
        "users": users,
        "display_name_backfilled": display_backfilled,
        "normalized_emails_valid": normalized_valid,
        "old_query_compatible": old_query_compatible(conn) if table_exists(conn, "users") else False,
    }


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def dump_schema(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    return "\n\n".join(row["sql"] + ";" for row in rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SQLite migration teaching demo")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--seed", type=Path)
    parser.add_argument("--target", type=int, default=3)
    parser.add_argument("--rollback-to", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    args.db.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(args.db)
    try:
        applied = migrate_to(conn, target=1)
        seeded = 0
        if args.seed and conn.execute("SELECT count(*) FROM users").fetchone()[0] == 0:
            seeded = seed_users(conn, args.seed)
        applied.extend(migrate_to(conn, target=args.target))
        rolled: list[int] = []
        if args.rollback_to is not None:
            rolled = rollback_to(conn, args.rollback_to)
        report = migration_report(conn)
        report.update({"newly_applied": applied, "rolled_back": rolled, "seeded": seeded})
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("SCHEMA_VERSION=%s" % report["schema_version"])
            print("USER_VERSION=%s" % report["user_version"])
            print("MIGRATIONS_APPLIED=%s" % len(report["applied_migrations"]))
            print("USERS=%s" % report["users"])
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
