from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from retry_idempotency_demo import (  # noqa: E402
    AlwaysPermanentFailure,
    CrashAfterSideEffect,
    FailsOnceThenSucceeds,
    IdempotencyConflict,
    PermanentError,
    count_app_rows,
    count_gateway_rows,
    create_order_with_idempotency,
    dispatch_one_outbox,
    naive_charge_request,
    reset_databases,
    retry_with_policy,
)


class RetryIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="retry-idem-test-")
        root = Path(self.temporary.name)
        self.app_db = root / "app.sqlite3"
        self.gateway_db = root / "gateway.sqlite3"
        reset_databases(self.app_db, self.gateway_db)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_naive_retry_duplicates_external_effect(self) -> None:
        with self.assertRaises(CrashAfterSideEffect):
            naive_charge_request(
                self.app_db,
                self.gateway_db,
                request_id="req-1",
                attempt_id="a",
                amount_cents=500,
                crash_after_effect=True,
            )
        naive_charge_request(
            self.app_db,
            self.gateway_db,
            request_id="req-1",
            attempt_id="b",
            amount_cents=500,
        )
        self.assertEqual(count_gateway_rows(self.gateway_db)["non_idempotent_effects"], 2)
        self.assertEqual(count_app_rows(self.app_db)["receipts"], 1)

    def test_idempotency_key_replays_same_response_and_conflicts_on_different_payload(self) -> None:
        first = create_order_with_idempotency(
            self.app_db, idempotency_key="idem-1", customer_id="cust-1", amount_cents=700
        )
        second = create_order_with_idempotency(
            self.app_db, idempotency_key="idem-1", customer_id="cust-1", amount_cents=700
        )
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.response, second.response)
        self.assertEqual(count_app_rows(self.app_db)["outbox_total"], 1)
        with self.assertRaises(IdempotencyConflict):
            create_order_with_idempotency(
                self.app_db, idempotency_key="idem-1", customer_id="cust-1", amount_cents=701
            )

    def test_outbox_without_receiver_dedupe_can_duplicate_after_dispatcher_crash(self) -> None:
        create_order_with_idempotency(
            self.app_db, idempotency_key="idem-2", customer_id="cust-1", amount_cents=800
        )
        with self.assertRaises(CrashAfterSideEffect):
            dispatch_one_outbox(
                self.app_db, self.gateway_db, receiver_mode="non_idempotent", crash_after_send=True
            )
        dispatch_one_outbox(self.app_db, self.gateway_db, receiver_mode="non_idempotent")
        self.assertEqual(count_gateway_rows(self.gateway_db)["non_idempotent_effects"], 2)
        self.assertEqual(count_app_rows(self.app_db)["outbox_sent"], 1)

    def test_stable_event_id_and_receiver_dedupe_apply_once_after_dispatcher_crash(self) -> None:
        create_order_with_idempotency(
            self.app_db, idempotency_key="idem-3", customer_id="cust-1", amount_cents=900
        )
        with self.assertRaises(CrashAfterSideEffect):
            dispatch_one_outbox(
                self.app_db, self.gateway_db, receiver_mode="idempotent", crash_after_send=True
            )
        dispatch_one_outbox(self.app_db, self.gateway_db, receiver_mode="idempotent")
        gateway = count_gateway_rows(self.gateway_db)
        self.assertEqual(gateway["idempotent_effects"], 1)
        self.assertEqual(gateway["idempotent_deliveries"], 2)
        self.assertEqual(gateway["idempotent_duplicate_deliveries"], 1)
        self.assertEqual(count_app_rows(self.app_db)["outbox_sent"], 1)

    def test_retry_policy_retries_transient_but_not_permanent(self) -> None:
        flaky = FailsOnceThenSucceeds()
        result, attempts = retry_with_policy(flaky, max_attempts=3)
        self.assertEqual(result, "ok")
        self.assertEqual(attempts, 2)
        permanent = AlwaysPermanentFailure()
        with self.assertRaises(PermanentError):
            retry_with_policy(permanent, max_attempts=3)
        self.assertEqual(permanent.calls, 1)


if __name__ == "__main__":
    unittest.main()
