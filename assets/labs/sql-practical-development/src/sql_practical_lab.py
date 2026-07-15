#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

VALID_STATUSES = {"open", "in_progress", "done"}

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived'))
);
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'developer'
);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    assignee_id INTEGER REFERENCES members(id) ON DELETE SET NULL,
    title TEXT NOT NULL CHECK (length(title) > 0),
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'done')),
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    estimate_hours REAL NOT NULL DEFAULT 1.0 CHECK (estimate_hours >= 0),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_events (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tickets_status_priority
    ON tickets(status, priority DESC, id);
CREATE INDEX IF NOT EXISTS idx_tickets_project_status
    ON tickets(project_id, status);
CREATE INDEX IF NOT EXISTS idx_events_ticket
    ON ticket_events(ticket_id, occurred_at);
"""

PROJECTS = [
    ("blog-platform", "active"),
    ("lab-runner", "active"),
    ("research-notes", "active"),
]
MEMBERS = [
    ("Alice", "maintainer"),
    ("Bo", "developer"),
    ("Chen", "reviewer"),
]
TICKETS = [
    ("blog-platform", "Fix column order", "done", 2, "Alice", 1.5, "2026-06-26T09:00:00Z"),
    ("blog-platform", "Write SQL route", "open", 3, "Alice", 2.0, "2026-06-28T08:00:00Z"),
    ("blog-platform", "Check public markers", "in_progress", 1, "Chen", 1.0, "2026-06-28T08:20:00Z"),
    ("lab-runner", "Add transaction demo", "open", 4, "Bo", 3.0, "2026-06-28T09:00:00Z"),
    ("lab-runner", "Export JSON and CSV", "done", 2, "Bo", 2.5, "2026-06-27T18:00:00Z"),
    ("research-notes", "Summarize baseline gap", "open", 5, None, 4.0, "2026-06-28T10:00:00Z"),
]

QUERY_SQL = {
    "open_tickets": """
        SELECT p.name AS project, t.id, t.title, t.status, t.priority,
               COALESCE(m.name, 'unassigned') AS assignee
        FROM tickets AS t
        JOIN projects AS p ON p.id = t.project_id
        LEFT JOIN members AS m ON m.id = t.assignee_id
        WHERE t.status <> 'done'
        ORDER BY t.priority DESC, t.id ASC;
    """,
    "project_summary": """
        SELECT p.name AS project,
               COUNT(t.id) AS total_tickets,
               SUM(CASE WHEN t.status <> 'done' THEN 1 ELSE 0 END) AS open_tickets,
               ROUND(SUM(t.estimate_hours), 1) AS estimated_hours
        FROM projects AS p
        LEFT JOIN tickets AS t ON t.project_id = p.id
        GROUP BY p.id, p.name
        ORDER BY open_tickets DESC, p.name ASC;
    """,
    "workload": """
        SELECT COALESCE(m.name, 'unassigned') AS assignee,
               COUNT(t.id) AS active_tickets,
               ROUND(SUM(t.estimate_hours), 1) AS active_hours
        FROM tickets AS t
        LEFT JOIN members AS m ON m.id = t.assignee_id
        WHERE t.status <> 'done'
        GROUP BY m.id, m.name
        ORDER BY active_hours DESC, assignee ASC;
    """,
    "priority_open": """
        SELECT id, title, priority
        FROM tickets
        WHERE status = ? AND priority >= ?
        ORDER BY priority DESC, id ASC;
    """,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    with conn:
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (1, now_iso()),
        )


def _lookup_id(conn: sqlite3.Connection, table: str, name: str) -> int:
    if table not in {"projects", "members"}:
        raise ValueError(f"unsupported lookup table: {table}")
    row = conn.execute(f"SELECT id FROM {table} WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise ValueError(f"unknown {table[:-1]}: {name}")
    return int(row["id"])


def seed(conn: sqlite3.Connection) -> None:
    migrate(conn)
    with conn:
        conn.execute("DELETE FROM ticket_events")
        conn.execute("DELETE FROM tickets")
        conn.execute("DELETE FROM members")
        conn.execute("DELETE FROM projects")
        conn.executemany("INSERT INTO projects(name, status) VALUES (?, ?)", PROJECTS)
        conn.executemany("INSERT INTO members(name, role) VALUES (?, ?)", MEMBERS)
        for project, title, status, priority, assignee, estimate, created_at in TICKETS:
            project_id = _lookup_id(conn, "projects", project)
            assignee_id = _lookup_id(conn, "members", assignee) if assignee else None
            cur = conn.execute(
                """
                INSERT INTO tickets(project_id, assignee_id, title, status, priority, estimate_hours, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, assignee_id, title, status, priority, estimate, created_at),
            )
            conn.execute(
                "INSERT INTO ticket_events(ticket_id, event_type, note, occurred_at) VALUES (?, ?, ?, ?)",
                (cur.lastrowid, "seed", f"seeded ticket {title}", created_at),
            )


def rows_as_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, object]]:
    return [dict(row) for row in rows]


def run_named_query(conn: sqlite3.Connection, name: str) -> list[dict[str, object]]:
    if name not in QUERY_SQL or name == "priority_open":
        raise ValueError(f"unknown report query: {name}")
    return rows_as_dicts(conn.execute(QUERY_SQL[name]).fetchall())


def add_ticket(
    conn: sqlite3.Connection,
    *,
    project: str,
    title: str,
    priority: int,
    assignee: str | None = None,
    status: str = "open",
    estimate_hours: float = 1.0,
) -> int:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    project_id = _lookup_id(conn, "projects", project)
    assignee_id = _lookup_id(conn, "members", assignee) if assignee else None
    with conn:
        cur = conn.execute(
            """
            INSERT INTO tickets(project_id, assignee_id, title, status, priority, estimate_hours, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, assignee_id, title, status, priority, estimate_hours, now_iso()),
        )
        ticket_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO ticket_events(ticket_id, event_type, note, occurred_at) VALUES (?, ?, ?, ?)",
            (ticket_id, "created", "created by parameterized query", now_iso()),
        )
    return ticket_id


def update_ticket_status(conn: sqlite3.Connection, ticket_id: int, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    with conn:
        cur = conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
        if cur.rowcount != 1:
            raise ValueError(f"ticket not found: {ticket_id}")
        conn.execute(
            "INSERT INTO ticket_events(ticket_id, event_type, note, occurred_at) VALUES (?, ?, ?, ?)",
            (ticket_id, "status", f"status changed to {status}", now_iso()),
        )


def delete_done_tickets(conn: sqlite3.Connection) -> int:
    with conn:
        cur = conn.execute("DELETE FROM tickets WHERE status = ?", ("done",))
    return int(cur.rowcount)


def import_tickets_csv(conn: sqlite3.Connection, csv_path: Path | str) -> list[int]:
    created: list[int] = []
    with Path(csv_path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"project", "title", "priority", "assignee"}
        if set(reader.fieldnames or []) != required:
            raise ValueError(f"CSV header must be exactly {sorted(required)}")
        for row in reader:
            created.append(
                add_ticket(
                    conn,
                    project=row["project"],
                    title=row["title"],
                    priority=int(row["priority"]),
                    assignee=row["assignee"] or None,
                )
            )
    return created


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def export_reports(conn: sqlite3.Connection, out_dir: Path | str) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": now_iso(),
        "project_summary": run_named_query(conn, "project_summary"),
        "workload": run_named_query(conn, "workload"),
        "open_tickets": run_named_query(conn, "open_tickets"),
    }
    json_path = out / "report.json"
    _atomic_write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    csv_path = out / "open_tickets.csv"
    rows = report["open_tickets"]
    tmp = csv_path.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["project", "id", "title", "status", "priority", "assignee"])
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(csv_path)
    return {"json": json_path, "csv": csv_path}


def explain_priority_query(conn: sqlite3.Connection) -> list[dict[str, object]]:
    rows = conn.execute("EXPLAIN QUERY PLAN " + QUERY_SQL["priority_open"], ("open", 3)).fetchall()
    return rows_as_dicts(rows)


def transaction_rollback_demo(conn: sqlite3.Connection) -> dict[str, object]:
    before = int(conn.execute("SELECT COUNT(*) AS n FROM tickets").fetchone()["n"])
    rolled_back = False
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO tickets(project_id, title, status, priority, estimate_hours, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (_lookup_id(conn, "projects", "blog-platform"), "Temporary transaction ticket", "open", 3, 1.0, now_iso()),
            )
            conn.execute(
                """
                INSERT INTO tickets(project_id, title, status, priority, estimate_hours, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (999999, "Broken foreign key", "open", 3, 1.0, now_iso()),
            )
    except sqlite3.IntegrityError:
        rolled_back = True
    after = int(conn.execute("SELECT COUNT(*) AS n FROM tickets").fetchone()["n"])
    return {"before": before, "after": after, "rolled_back": rolled_back}


def format_table(rows: Sequence[dict[str, object]]) -> str:
    if not rows:
        return "(no rows)"
    columns = list(rows[0].keys())
    widths = {col: max(len(col), *(len(str(row[col])) for row in rows)) for col in columns}
    lines = [" | ".join(col.ljust(widths[col]) for col in columns)]
    lines.append("-+-".join("-" * widths[col] for col in columns))
    for row in rows:
        lines.append(" | ".join(str(row[col]).ljust(widths[col]) for col in columns))
    return "\n".join(lines)


def write_markdown_report(conn: sqlite3.Connection, reports_dir: Path, exports: dict[str, Path]) -> Path:
    plan = explain_priority_query(conn)
    rollback = transaction_rollback_demo(conn)
    lines = [
        "# SQL Practical Development Lab Report",
        "",
        f"- SQLite library version: {sqlite3.sqlite_version}",
        f"- Open ticket rows: {len(run_named_query(conn, 'open_tickets'))}",
        f"- Transaction rollback preserved row count: {rollback['before']} -> {rollback['after']}",
        f"- JSON export: `{exports['json'].name}`",
        f"- CSV export: `{exports['csv'].name}`",
        "",
        "## Project summary",
        "",
        "```text",
        format_table(run_named_query(conn, "project_summary")),
        "```",
        "",
        "## Query plan for priority_open",
        "",
        "```text",
    ]
    lines.extend(str(row["detail"]) for row in plan)
    lines.extend(["```", ""])
    report_path = reports_dir / "sql_lab_report.md"
    _atomic_write_text(report_path, "\n".join(lines))
    return report_path


def run_all(db_path: Path, reports_dir: Path, import_csv: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    with connect(db_path) as conn:
        migrate(conn)
        seed(conn)
        created = import_tickets_csv(conn, import_csv)
        open_rows = run_named_query(conn, "open_tickets")
        project_rows = run_named_query(conn, "project_summary")
        workload_rows = run_named_query(conn, "workload")
        plan = explain_priority_query(conn)
        rollback = transaction_rollback_demo(conn)
        exports = export_reports(conn, reports_dir)
        report_path = write_markdown_report(conn, reports_dir, exports)
    print(f"database={db_path}")
    print(f"sqlite_version={sqlite3.sqlite_version}")
    print(f"imported_tickets={len(created)}")
    print(f"open_tickets={len(open_rows)}")
    print(f"project_summary_rows={len(project_rows)}")
    print(f"workload_rows={len(workload_rows)}")
    print(f"rollback_before={rollback['before']} rollback_after={rollback['after']} rolled_back={rollback['rolled_back']}")
    print("query_plan=" + " || ".join(str(row["detail"]) for row in plan))
    print(f"json_export={exports['json']}")
    print(f"csv_export={exports['csv']}")
    print(f"markdown_report={report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Practical SQL development lab")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create schema in a SQLite database")
    p_init.add_argument("--db", type=Path, required=True)

    p_seed = sub.add_parser("seed", help="Seed deterministic sample data")
    p_seed.add_argument("--db", type=Path, required=True)

    p_query = sub.add_parser("query", help="Run a named report query")
    p_query.add_argument("--db", type=Path, required=True)
    p_query.add_argument("--name", choices=["open_tickets", "project_summary", "workload"], required=True)

    p_add = sub.add_parser("add-ticket", help="Add a ticket with a parameterized INSERT")
    p_add.add_argument("--db", type=Path, required=True)
    p_add.add_argument("--project", required=True)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--priority", type=int, default=3)
    p_add.add_argument("--assignee")

    p_status = sub.add_parser("status", help="Update ticket status")
    p_status.add_argument("--db", type=Path, required=True)
    p_status.add_argument("--ticket-id", type=int, required=True)
    p_status.add_argument("--status", choices=sorted(VALID_STATUSES), required=True)

    p_delete = sub.add_parser("delete-done", help="Delete tickets whose status is done")
    p_delete.add_argument("--db", type=Path, required=True)

    p_import = sub.add_parser("import-csv", help="Import tickets from CSV")
    p_import.add_argument("--db", type=Path, required=True)
    p_import.add_argument("--csv", type=Path, required=True)

    p_export = sub.add_parser("export", help="Export JSON and CSV reports")
    p_export.add_argument("--db", type=Path, required=True)
    p_export.add_argument("--out", type=Path, required=True)

    p_explain = sub.add_parser("explain", help="Show EXPLAIN QUERY PLAN output")
    p_explain.add_argument("--db", type=Path, required=True)

    p_tx = sub.add_parser("transaction-demo", help="Demonstrate rollback on a failed multi-step change")
    p_tx.add_argument("--db", type=Path, required=True)

    p_all = sub.add_parser("run-all", help="Run full capstone scenario")
    p_all.add_argument("--db", type=Path, required=True)
    p_all.add_argument("--reports", type=Path, required=True)
    p_all.add_argument("--import-csv", type=Path, default=Path("sample_import/new_tickets.csv"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run-all":
        run_all(args.db, args.reports, args.import_csv)
        return 0
    with connect(args.db) as conn:
        if args.command == "init":
            migrate(conn)
            print(f"initialized {args.db}")
        elif args.command == "seed":
            seed(conn)
            print("seeded projects=3 members=3 tickets=6")
        elif args.command == "query":
            print(format_table(run_named_query(conn, args.name)))
        elif args.command == "add-ticket":
            ticket_id = add_ticket(conn, project=args.project, title=args.title, priority=args.priority, assignee=args.assignee)
            print(f"created ticket id={ticket_id}")
        elif args.command == "status":
            update_ticket_status(conn, args.ticket_id, args.status)
            print(f"ticket {args.ticket_id} status={args.status}")
        elif args.command == "delete-done":
            print(f"deleted={delete_done_tickets(conn)}")
        elif args.command == "import-csv":
            print(f"imported={len(import_tickets_csv(conn, args.csv))}")
        elif args.command == "export":
            exports = export_reports(conn, args.out)
            print(f"json={exports['json']}")
            print(f"csv={exports['csv']}")
        elif args.command == "explain":
            for row in explain_priority_query(conn):
                print(row["detail"])
        elif args.command == "transaction-demo":
            print(json.dumps(transaction_rollback_demo(conn), sort_keys=True))
        else:
            parser.error(f"unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
