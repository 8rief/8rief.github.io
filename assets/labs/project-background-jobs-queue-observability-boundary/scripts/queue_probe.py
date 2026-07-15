#!/usr/bin/env python3
"""Generate deterministic queue/worker observability evidence."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
REPORTS = ROOT / "reports"
sys.path.insert(0, str(SRC))

from job_queue_demo import (  # noqa: E402
    complete_job,
    enqueue_job,
    fail_job,
    get_job,
    heartbeat,
    lease_job,
    read_jsonl_events,
    reset_db,
    status_report,
)


def new_paths(root: Path, name: str) -> tuple[Path, Path]:
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    db = directory / "queue.sqlite3"
    log = directory / "events.jsonl"
    reset_db(db)
    log.unlink(missing_ok=True)
    return db, log


def enqueue(db: Path, log: Path, job_id: str, *, max_attempts: int = 3, now: int = 0) -> None:
    enqueue_job(db, log, job_id=job_id, kind="demo", payload={"job_id": job_id}, max_attempts=max_attempts, now=now)


def scenario_exclusive(root: Path) -> dict[str, Any]:
    db, log = new_paths(root, "exclusive")
    enqueue(db, log, "job-exclusive")
    first = lease_job(db, log, worker_id="worker-a", now=0, lease_seconds=10)
    second = lease_job(db, log, worker_id="worker-b", now=0, lease_seconds=10)
    return {
        "first_worker_leased": first is not None,
        "second_worker_got_none": second is None,
        "job": get_job(db, "job-exclusive"),
        "status": status_report(db, now=0),
        "events": read_jsonl_events(log),
    }


def scenario_reclaim(root: Path) -> dict[str, Any]:
    db, log = new_paths(root, "reclaim")
    enqueue(db, log, "job-reclaim")
    lease_job(db, log, worker_id="worker-a", now=0, lease_seconds=10)
    before = lease_job(db, log, worker_id="worker-b", now=5, lease_seconds=10)
    after = lease_job(db, log, worker_id="worker-b", now=11, lease_seconds=10)
    return {
        "before_timeout_none": before is None,
        "after_timeout_reclaimed": after is not None and after.reclaimed,
        "attempts_after_reclaim": after.attempts if after else None,
        "job": get_job(db, "job-reclaim"),
        "status": status_report(db, now=11),
        "events": read_jsonl_events(log),
    }


def scenario_heartbeat(root: Path) -> dict[str, Any]:
    db, log = new_paths(root, "heartbeat")
    enqueue(db, log, "job-heartbeat")
    lease_job(db, log, worker_id="worker-a", now=0, lease_seconds=10)
    extended_until = heartbeat(db, log, job_id="job-heartbeat", worker_id="worker-a", now=7, lease_seconds=10)
    early = lease_job(db, log, worker_id="worker-b", now=12, lease_seconds=10)
    late = lease_job(db, log, worker_id="worker-b", now=18, lease_seconds=10)
    return {
        "extended_until": extended_until,
        "early_reclaim_none": early is None,
        "late_reclaim_succeeded": late is not None and late.reclaimed,
        "job": get_job(db, "job-heartbeat"),
        "status": status_report(db, now=18),
        "events": read_jsonl_events(log),
    }


def scenario_retry_success(root: Path) -> dict[str, Any]:
    db, log = new_paths(root, "retry-success")
    enqueue(db, log, "job-transient", max_attempts=3)
    lease_job(db, log, worker_id="worker-a", now=0, lease_seconds=10)
    fail_job(
        db,
        log,
        job_id="job-transient",
        worker_id="worker-a",
        error="temporary service unavailable",
        transient=True,
        now=1,
        base_backoff_seconds=5,
    )
    before = lease_job(db, log, worker_id="worker-b", now=5, lease_seconds=10)
    retry = lease_job(db, log, worker_id="worker-b", now=6, lease_seconds=10)
    complete_job(db, log, job_id="job-transient", worker_id="worker-b", result={"ok": True}, now=7)
    return {
        "before_backoff_none": before is None,
        "retry_attempts": retry.attempts if retry else None,
        "job": get_job(db, "job-transient"),
        "status": status_report(db, now=7),
        "events": read_jsonl_events(log),
    }


def scenario_dead_letters(root: Path) -> dict[str, Any]:
    db, log = new_paths(root, "dead-letters")
    enqueue(db, log, "job-permanent", max_attempts=3)
    lease_job(db, log, worker_id="worker-a", now=0, lease_seconds=10)
    permanent_state = fail_job(
        db,
        log,
        job_id="job-permanent",
        worker_id="worker-a",
        error="invalid payload",
        transient=False,
        now=1,
    )
    enqueue(db, log, "job-exhausted", max_attempts=2, now=2)
    lease_job(db, log, worker_id="worker-a", now=2, lease_seconds=10)
    fail_job(
        db,
        log,
        job_id="job-exhausted",
        worker_id="worker-a",
        error="temporary service unavailable",
        transient=True,
        now=3,
        base_backoff_seconds=1,
    )
    lease_job(db, log, worker_id="worker-b", now=4, lease_seconds=10)
    exhausted_state = fail_job(
        db,
        log,
        job_id="job-exhausted",
        worker_id="worker-b",
        error="temporary service unavailable again",
        transient=True,
        now=5,
        base_backoff_seconds=1,
    )
    return {
        "permanent_state": permanent_state,
        "exhausted_state": exhausted_state,
        "permanent_job": get_job(db, "job-permanent"),
        "exhausted_job": get_job(db, "job-exhausted"),
        "status": status_report(db, now=5),
        "events": read_jsonl_events(log),
    }


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="job-queue-observability-") as tmp:
        root = Path(tmp)
        report = {
            "schema_version": 1,
            "exclusive_lease": scenario_exclusive(root),
            "visibility_timeout_reclaim": scenario_reclaim(root),
            "heartbeat_extension": scenario_heartbeat(root),
            "transient_retry_success": scenario_retry_success(root),
            "dead_letter": scenario_dead_letters(root),
        }
    all_events = []
    for scenario in report.values():
        if isinstance(scenario, dict) and "events" in scenario:
            all_events.extend(scenario["events"])
    checks = {
        "ready_job_claimed_once": report["exclusive_lease"]["first_worker_leased"]
        and report["exclusive_lease"]["second_worker_got_none"],
        "expired_job_reclaimed": report["visibility_timeout_reclaim"]["before_timeout_none"]
        and report["visibility_timeout_reclaim"]["after_timeout_reclaimed"]
        and report["visibility_timeout_reclaim"]["attempts_after_reclaim"] == 2,
        "heartbeat_prevented_early_reclaim": report["heartbeat_extension"]["early_reclaim_none"]
        and report["heartbeat_extension"]["late_reclaim_succeeded"]
        and report["heartbeat_extension"]["extended_until"] == 17,
        "transient_retry_succeeded": report["transient_retry_success"]["before_backoff_none"]
        and report["transient_retry_success"]["retry_attempts"] == 2
        and report["transient_retry_success"]["job"]["state"] == "succeeded",
        "permanent_dead_lettered": report["dead_letter"]["permanent_state"] == "dead"
        and report["dead_letter"]["permanent_job"]["attempts"] == 1,
        "exhausted_dead_lettered": report["dead_letter"]["exhausted_state"] == "dead"
        and report["dead_letter"]["exhausted_job"]["attempts"] == 2,
        "jsonl_events_valid": all(event.get("schema_version") == 1 and "event" in event for event in all_events),
    }
    if not all(checks.values()):
        raise AssertionError(json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True))
    report["checks"] = checks
    report["event_count"] = len(all_events)
    (REPORTS / "queue_probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    transcript = [
        "# Background job queue transcript",
        "",
        "```text",
        "READY_JOB_CLAIMED_ONCE=yes",
        "EXPIRED_JOB_RECLAIMED=yes",
        "HEARTBEAT_PREVENTED_EARLY_RECLAIM=yes",
        "TRANSIENT_RETRY_FINAL_STATE=succeeded",
        "TRANSIENT_RETRY_ATTEMPTS=2",
        "PERMANENT_DEAD_LETTER=yes",
        "MAX_ATTEMPTS_DEAD_LETTER=yes",
        f"EVENT_COUNT={len(all_events)}",
        "JSONL_EVENTS_VALID=yes",
        "RUN_STATUS=ok",
        "```",
        "",
    ]
    (REPORTS / "transcript.md").write_text("\n".join(transcript), encoding="utf-8")
    final_counts = report["dead_letter"]["status"]["counts"]
    (REPORTS / "queue_status_report.md").write_text(
        "# Queue status report\n\n"
        f"Dead-letter scenario counts: pending={final_counts['pending']}, running={final_counts['running']}, "
        f"succeeded={final_counts['succeeded']}, dead={final_counts['dead']}.\n\n"
        "The full JSON report includes per-scenario status snapshots and JSONL events for enqueue, lease, "
        "lease reclaim, heartbeat, retry scheduling, success, and dead-letter transitions.\n",
        encoding="utf-8",
    )
    for line in transcript[3:13]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
