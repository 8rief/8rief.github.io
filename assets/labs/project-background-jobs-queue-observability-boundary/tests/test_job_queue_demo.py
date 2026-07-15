from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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


class JobQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="queue-test-")
        root = Path(self.temporary.name)
        self.db = root / "queue.sqlite3"
        self.log = root / "events.jsonl"
        reset_db(self.db)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def enqueue(self, job_id: str, max_attempts: int = 3) -> None:
        enqueue_job(
            self.db,
            self.log,
            job_id=job_id,
            kind="demo",
            payload={"job_id": job_id},
            max_attempts=max_attempts,
            now=0,
        )

    def test_same_ready_job_is_leased_by_one_worker(self) -> None:
        self.enqueue("job-exclusive")
        first = lease_job(self.db, self.log, worker_id="worker-a", now=0, lease_seconds=10)
        second = lease_job(self.db, self.log, worker_id="worker-b", now=0, lease_seconds=10)
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(status_report(self.db, now=0)["counts"]["running"], 1)

    def test_expired_running_job_is_reclaimed_after_visibility_timeout(self) -> None:
        self.enqueue("job-reclaim")
        lease_job(self.db, self.log, worker_id="worker-a", now=0, lease_seconds=10)
        self.assertIsNone(lease_job(self.db, self.log, worker_id="worker-b", now=5, lease_seconds=10))
        reclaimed = lease_job(self.db, self.log, worker_id="worker-b", now=11, lease_seconds=10)
        self.assertIsNotNone(reclaimed)
        self.assertTrue(reclaimed.reclaimed)
        self.assertEqual(reclaimed.attempts, 2)
        self.assertEqual(get_job(self.db, "job-reclaim")["locked_by"], "worker-b")

    def test_heartbeat_extends_lease_and_prevents_early_reclaim(self) -> None:
        self.enqueue("job-heartbeat")
        lease_job(self.db, self.log, worker_id="worker-a", now=0, lease_seconds=10)
        self.assertEqual(heartbeat(self.db, self.log, job_id="job-heartbeat", worker_id="worker-a", now=7, lease_seconds=10), 17)
        self.assertIsNone(lease_job(self.db, self.log, worker_id="worker-b", now=12, lease_seconds=10))
        reclaimed = lease_job(self.db, self.log, worker_id="worker-b", now=18, lease_seconds=10)
        self.assertIsNotNone(reclaimed)
        self.assertTrue(reclaimed.reclaimed)

    def test_transient_failure_schedules_retry_then_succeeds(self) -> None:
        self.enqueue("job-transient")
        lease_job(self.db, self.log, worker_id="worker-a", now=0, lease_seconds=10)
        self.assertEqual(
            fail_job(
                self.db,
                self.log,
                job_id="job-transient",
                worker_id="worker-a",
                error="temporary service unavailable",
                transient=True,
                now=1,
                base_backoff_seconds=5,
            ),
            "pending",
        )
        self.assertIsNone(lease_job(self.db, self.log, worker_id="worker-b", now=5, lease_seconds=10))
        retry = lease_job(self.db, self.log, worker_id="worker-b", now=6, lease_seconds=10)
        self.assertIsNotNone(retry)
        self.assertEqual(retry.attempts, 2)
        complete_job(self.db, self.log, job_id="job-transient", worker_id="worker-b", result={"ok": True}, now=7)
        self.assertEqual(get_job(self.db, "job-transient")["state"], "succeeded")

    def test_permanent_failure_goes_to_dead_without_retry(self) -> None:
        self.enqueue("job-permanent", max_attempts=3)
        lease_job(self.db, self.log, worker_id="worker-a", now=0, lease_seconds=10)
        self.assertEqual(
            fail_job(
                self.db,
                self.log,
                job_id="job-permanent",
                worker_id="worker-a",
                error="invalid payload",
                transient=False,
                now=1,
            ),
            "dead",
        )
        self.assertIsNone(lease_job(self.db, self.log, worker_id="worker-b", now=100, lease_seconds=10))
        self.assertEqual(get_job(self.db, "job-permanent")["attempts"], 1)

    def test_exhausted_attempts_go_to_dead_letter(self) -> None:
        self.enqueue("job-exhausted", max_attempts=2)
        lease_job(self.db, self.log, worker_id="worker-a", now=0, lease_seconds=10)
        fail_job(
            self.db,
            self.log,
            job_id="job-exhausted",
            worker_id="worker-a",
            error="temporary service unavailable",
            transient=True,
            now=1,
            base_backoff_seconds=1,
        )
        lease_job(self.db, self.log, worker_id="worker-b", now=2, lease_seconds=10)
        self.assertEqual(
            fail_job(
                self.db,
                self.log,
                job_id="job-exhausted",
                worker_id="worker-b",
                error="temporary service unavailable again",
                transient=True,
                now=3,
                base_backoff_seconds=1,
            ),
            "dead",
        )
        self.assertEqual(get_job(self.db, "job-exhausted")["attempts"], 2)

    def test_jsonl_events_and_status_report_are_observable(self) -> None:
        self.enqueue("job-status")
        lease_job(self.db, self.log, worker_id="worker-a", now=0, lease_seconds=10)
        complete_job(self.db, self.log, job_id="job-status", worker_id="worker-a", result={"ok": True}, now=1)
        events = read_jsonl_events(self.log)
        self.assertEqual([event["event"] for event in events], ["job_enqueued", "job_leased", "job_succeeded"])
        report = status_report(self.db, now=1)
        self.assertEqual(report["counts"]["succeeded"], 1)
        self.assertEqual(report["total_attempts"], 1)


if __name__ == "__main__":
    unittest.main()
