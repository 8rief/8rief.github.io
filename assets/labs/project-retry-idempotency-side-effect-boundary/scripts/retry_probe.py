#!/usr/bin/env python3
"""Generate deterministic reports for retry and side-effect boundary demos."""

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

from retry_idempotency_demo import (  # noqa: E402
    AlwaysPermanentFailure,
    CrashAfterSideEffect,
    FailsOnceThenSucceeds,
    IdempotencyConflict,
    RC_IDEMPOTENCY_CONFLICT,
    count_app_rows,
    count_gateway_rows,
    create_order_with_idempotency,
    dispatch_one_outbox,
    naive_charge_request,
    reset_databases,
    retry_with_policy,
)


def app_db(run: Path) -> Path:
    return run / "app.sqlite3"


def gateway_db(run: Path) -> Path:
    return run / "gateway.sqlite3"


def scenario_naive(run: Path) -> dict[str, Any]:
    reset_databases(app_db(run), gateway_db(run))
    crashed = False
    try:
        naive_charge_request(
            app_db(run),
            gateway_db(run),
            request_id="req-naive-1",
            attempt_id="first",
            amount_cents=500,
            crash_after_effect=True,
        )
    except CrashAfterSideEffect:
        crashed = True
    naive_charge_request(
        app_db(run),
        gateway_db(run),
        request_id="req-naive-1",
        attempt_id="retry",
        amount_cents=500,
    )
    return {
        "first_attempt_crashed_after_effect": crashed,
        "app": count_app_rows(app_db(run)),
        "gateway": count_gateway_rows(gateway_db(run)),
    }


def scenario_request_idempotency(run: Path) -> dict[str, Any]:
    reset_databases(app_db(run), gateway_db(run))
    first = create_order_with_idempotency(
        app_db(run), idempotency_key="pay-20260705-001", customer_id="cust-1", amount_cents=700
    )
    second = create_order_with_idempotency(
        app_db(run), idempotency_key="pay-20260705-001", customer_id="cust-1", amount_cents=700
    )
    conflict = False
    conflict_code = None
    try:
        create_order_with_idempotency(
            app_db(run), idempotency_key="pay-20260705-001", customer_id="cust-1", amount_cents=701
        )
    except IdempotencyConflict:
        conflict = True
        conflict_code = RC_IDEMPOTENCY_CONFLICT
    return {
        "first_replayed": first.replayed,
        "second_replayed": second.replayed,
        "same_response": first.response == second.response,
        "conflict_detected": conflict,
        "conflict_return_code": conflict_code,
        "response": first.response,
        "app": count_app_rows(app_db(run)),
        "gateway": count_gateway_rows(gateway_db(run)),
    }


def scenario_outbox_without_receiver_dedupe(run: Path) -> dict[str, Any]:
    reset_databases(app_db(run), gateway_db(run))
    create_order_with_idempotency(
        app_db(run), idempotency_key="pay-20260705-002", customer_id="cust-1", amount_cents=800
    )
    crashed = False
    try:
        dispatch_one_outbox(
            app_db(run), gateway_db(run), receiver_mode="non_idempotent", crash_after_send=True
        )
    except CrashAfterSideEffect:
        crashed = True
    dispatch_one_outbox(app_db(run), gateway_db(run), receiver_mode="non_idempotent")
    return {
        "dispatcher_crashed_after_send": crashed,
        "app": count_app_rows(app_db(run)),
        "gateway": count_gateway_rows(gateway_db(run)),
    }


def scenario_stable_side_effect(run: Path) -> dict[str, Any]:
    reset_databases(app_db(run), gateway_db(run))
    create_order_with_idempotency(
        app_db(run), idempotency_key="pay-20260705-003", customer_id="cust-1", amount_cents=900
    )
    crashed = False
    try:
        dispatch_one_outbox(app_db(run), gateway_db(run), receiver_mode="idempotent", crash_after_send=True)
    except CrashAfterSideEffect:
        crashed = True
    dispatch_one_outbox(app_db(run), gateway_db(run), receiver_mode="idempotent")
    return {
        "dispatcher_crashed_after_send": crashed,
        "app": count_app_rows(app_db(run)),
        "gateway": count_gateway_rows(gateway_db(run)),
    }


def scenario_retry_policy() -> dict[str, Any]:
    transient = FailsOnceThenSucceeds()
    transient_result, transient_attempts = retry_with_policy(transient, max_attempts=3)
    permanent = AlwaysPermanentFailure()
    permanent_failed = False
    try:
        retry_with_policy(permanent, max_attempts=3)
    except Exception:
        permanent_failed = True
    return {
        "transient_result": transient_result,
        "transient_attempts": transient_attempts,
        "permanent_failed": permanent_failed,
        "permanent_attempts": permanent.calls,
    }


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="retry-idempotency-") as tmp:
        root = Path(tmp)
        report = {
            "schema_version": 1,
            "naive_retry": scenario_naive(root / "naive"),
            "request_idempotency": scenario_request_idempotency(root / "request-idempotency"),
            "outbox_without_receiver_dedupe": scenario_outbox_without_receiver_dedupe(root / "outbox-only"),
            "stable_side_effect_idempotency": scenario_stable_side_effect(root / "stable-side-effect"),
            "retry_policy": scenario_retry_policy(),
        }
    checks = {
        "naive_duplicate_effect": report["naive_retry"]["gateway"]["non_idempotent_effects"] == 2,
        "naive_local_receipt_once": report["naive_retry"]["app"]["receipts"] == 1,
        "request_replay_same_response": report["request_idempotency"]["same_response"]
        and report["request_idempotency"]["second_replayed"],
        "request_conflict_detected": report["request_idempotency"]["conflict_return_code"] == RC_IDEMPOTENCY_CONFLICT,
        "outbox_only_duplicate_effect": report["outbox_without_receiver_dedupe"]["gateway"][
            "non_idempotent_effects"
        ]
        == 2,
        "stable_event_applied_once": report["stable_side_effect_idempotency"]["gateway"][
            "idempotent_effects"
        ]
        == 1,
        "stable_event_delivery_attempts_two": report["stable_side_effect_idempotency"]["gateway"][
            "idempotent_deliveries"
        ]
        == 2,
        "transient_retried": report["retry_policy"]["transient_attempts"] == 2,
        "permanent_not_retried": report["retry_policy"]["permanent_attempts"] == 1,
    }
    if not all(checks.values()):
        raise AssertionError(json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True))
    report["checks"] = checks
    (REPORTS / "retry_idempotency_probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    transcript = [
        "# Retry and idempotency transcript",
        "",
        "```text",
        "NAIVE_EXTERNAL_EFFECTS=2",
        "NAIVE_DUPLICATE_CHARGE=yes",
        "REQUEST_REPLAY_SAME_RESPONSE=yes",
        "REQUEST_CONFLICT_RC=74",
        "OUTBOX_ONLY_EXTERNAL_EFFECTS=2",
        "STABLE_EVENT_APPLIED_EFFECTS=1",
        "STABLE_EVENT_DELIVERY_ATTEMPTS=2",
        "TRANSIENT_ATTEMPTS=2",
        "PERMANENT_ATTEMPTS=1",
        "RUN_STATUS=ok",
        "```",
        "",
    ]
    (REPORTS / "transcript.md").write_text("\n".join(transcript), encoding="utf-8")
    (REPORTS / "side_effect_summary.md").write_text(
        "# Side-effect boundary summary\n\n"
        "A retry after a crash-after-effect produced two non-idempotent external effects. "
        "A request idempotency key replayed the stored response and rejected payload reuse with code 74. "
        "A transactional outbox avoided duplicate enqueue, but a dispatcher crash after send still duplicated "
        "a non-idempotent receiver. A stable event ID plus receiver dedupe recorded two deliveries and one applied effect. "
        "Transient failures were retried once; permanent failures were not retried.\n",
        encoding="utf-8",
    )
    for line in transcript[3:13]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
