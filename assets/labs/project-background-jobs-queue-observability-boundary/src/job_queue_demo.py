#!/usr/bin/env python3
"""A deterministic SQLite-backed background job queue demo."""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATES = ("pending", "running", "succeeded", "dead")


class QueueStateError(RuntimeError):
    """The requested queue transition is not valid for the current job state."""


@dataclass(frozen=True)
class JobLease:
    job_id: str
    attempts: int
    lease_until: int
    reclaimed: bool


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def append_event(log_path: Path, event: str, *, now: int, **fields: Any) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"schema_version": SCHEMA_VERSION, "event": event, "now": now, **fields}
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write(canonical_json(record) + "\n")


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode = WAL")
    return con


def init_db(path: Path) -> None:
    with _connect(path) as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                state TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL,
                available_at INTEGER NOT NULL,
                lease_until INTEGER,
                locked_by TEXT,
                heartbeat_at INTEGER,
                last_error TEXT,
                result_json TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_ready ON jobs(state, available_at, lease_until, job_id);
            """
        )


def reset_db(path: Path) -> None:
    path.unlink(missing_ok=True)
    init_db(path)


def enqueue_job(
    db_path: Path,
    log_path: Path,
    *,
    job_id: str,
    kind: str,
    payload: dict[str, Any],
    max_attempts: int,
    now: int,
) -> None:
    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")
    with _connect(db_path) as con:
        con.execute(
            """
            INSERT INTO jobs(job_id, kind, payload_json, state, attempts, max_attempts,
                             available_at, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', 0, ?, ?, ?, ?)
            """,
            (job_id, kind, canonical_json(payload), max_attempts, now, now, now),
        )
    append_event(log_path, "job_enqueued", now=now, job_id=job_id, kind=kind, max_attempts=max_attempts)


def lease_job(
    db_path: Path,
    log_path: Path,
    *,
    worker_id: str,
    now: int,
    lease_seconds: int,
) -> JobLease | None:
    if lease_seconds <= 0:
        raise ValueError("lease_seconds must be positive")
    con = _connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            """
            SELECT * FROM jobs
            WHERE attempts < max_attempts
              AND (
                (state = 'pending' AND available_at <= ?)
                OR (state = 'running' AND lease_until <= ?)
              )
            ORDER BY created_at, job_id
            LIMIT 1
            """,
            (now, now),
        ).fetchone()
        if row is None:
            con.commit()
            return None
        reclaimed = row["state"] == "running"
        attempts = int(row["attempts"]) + 1
        lease_until = now + lease_seconds
        con.execute(
            """
            UPDATE jobs
            SET state = 'running', attempts = ?, lease_until = ?, locked_by = ?,
                heartbeat_at = ?, updated_at = ?
            WHERE job_id = ?
            """,
            (attempts, lease_until, worker_id, now, now, row["job_id"]),
        )
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    if reclaimed:
        append_event(
            log_path,
            "lease_reclaimed",
            now=now,
            job_id=row["job_id"],
            previous_worker=row["locked_by"],
            worker_id=worker_id,
            previous_lease_until=row["lease_until"],
        )
    append_event(
        log_path,
        "job_leased",
        now=now,
        job_id=row["job_id"],
        worker_id=worker_id,
        attempts=attempts,
        lease_until=lease_until,
        reclaimed=reclaimed,
    )
    return JobLease(str(row["job_id"]), attempts, lease_until, reclaimed)


def heartbeat(db_path: Path, log_path: Path, *, job_id: str, worker_id: str, now: int, lease_seconds: int) -> int:
    lease_until = now + lease_seconds
    with _connect(db_path) as con:
        cur = con.execute(
            """
            UPDATE jobs
            SET heartbeat_at = ?, lease_until = ?, updated_at = ?
            WHERE job_id = ? AND state = 'running' AND locked_by = ? AND lease_until > ?
            """,
            (now, lease_until, now, job_id, worker_id, now),
        )
        if cur.rowcount != 1:
            raise QueueStateError("heartbeat requires an unexpired running lease held by the worker")
    append_event(log_path, "worker_heartbeat", now=now, job_id=job_id, worker_id=worker_id, lease_until=lease_until)
    return lease_until


def complete_job(
    db_path: Path,
    log_path: Path,
    *,
    job_id: str,
    worker_id: str,
    result: dict[str, Any],
    now: int,
) -> None:
    with _connect(db_path) as con:
        cur = con.execute(
            """
            UPDATE jobs
            SET state = 'succeeded', locked_by = NULL, lease_until = NULL, heartbeat_at = NULL,
                result_json = ?, updated_at = ?
            WHERE job_id = ? AND state = 'running' AND locked_by = ?
            """,
            (canonical_json(result), now, job_id, worker_id),
        )
        if cur.rowcount != 1:
            raise QueueStateError("complete requires a running lease held by the worker")
    append_event(log_path, "job_succeeded", now=now, job_id=job_id, worker_id=worker_id)


def fail_job(
    db_path: Path,
    log_path: Path,
    *,
    job_id: str,
    worker_id: str,
    error: str,
    transient: bool,
    now: int,
    base_backoff_seconds: int = 5,
) -> str:
    con = _connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None or row["state"] != "running" or row["locked_by"] != worker_id:
            raise QueueStateError("fail requires a running lease held by the worker")
        attempts = int(row["attempts"])
        if (not transient) or attempts >= int(row["max_attempts"]):
            next_state = "dead"
            available_at = int(row["available_at"])
            con.execute(
                """
                UPDATE jobs
                SET state = 'dead', locked_by = NULL, lease_until = NULL, heartbeat_at = NULL,
                    last_error = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (error, now, job_id),
            )
        else:
            next_state = "pending"
            available_at = now + base_backoff_seconds * attempts
            con.execute(
                """
                UPDATE jobs
                SET state = 'pending', locked_by = NULL, lease_until = NULL, heartbeat_at = NULL,
                    available_at = ?, last_error = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (available_at, error, now, job_id),
            )
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    if next_state == "pending":
        append_event(
            log_path,
            "job_retry_scheduled",
            now=now,
            job_id=job_id,
            worker_id=worker_id,
            attempts=attempts,
            available_at=available_at,
            error=error,
        )
    else:
        reason = "permanent" if not transient else "max_attempts"
        append_event(
            log_path,
            "job_dead_lettered",
            now=now,
            job_id=job_id,
            worker_id=worker_id,
            attempts=attempts,
            reason=reason,
            error=error,
        )
    return next_state


def get_job(db_path: Path, job_id: str) -> dict[str, Any]:
    with _connect(db_path) as con:
        row = con.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(job_id)
    return dict(row)


def status_report(db_path: Path, *, now: int) -> dict[str, Any]:
    with _connect(db_path) as con:
        counts = {state: 0 for state in STATES}
        for row in con.execute("SELECT state, COUNT(*) AS n FROM jobs GROUP BY state"):
            counts[str(row["state"])] = int(row["n"])
        ready = con.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE state = 'pending' AND available_at <= ?", (now,)
        ).fetchone()["n"]
        delayed = con.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE state = 'pending' AND available_at > ?", (now,)
        ).fetchone()["n"]
        expired = con.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE state = 'running' AND lease_until <= ?", (now,)
        ).fetchone()["n"]
        total_attempts = con.execute("SELECT COALESCE(SUM(attempts), 0) AS n FROM jobs").fetchone()["n"]
    return {
        "schema_version": SCHEMA_VERSION,
        "now": now,
        "counts": counts,
        "pending_ready": int(ready),
        "pending_delayed": int(delayed),
        "running_expired": int(expired),
        "total_attempts": int(total_attempts),
    }


def read_jsonl_events(log_path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not log_path.exists():
        return events
    for line in log_path.read_text(encoding="utf-8").splitlines():
        events.append(json.loads(line))
    return events


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init-db", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.init_db:
        init_db(args.init_db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
