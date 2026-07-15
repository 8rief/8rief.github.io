#!/usr/bin/env python3
"""Retry, idempotency-key, outbox, and side-effect boundary demo."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar


RC_IDEMPOTENCY_CONFLICT = 74
RC_PERMANENT_ERROR = 76
SCHEMA_VERSION = 1
T = TypeVar("T")


class CrashAfterSideEffect(RuntimeError):
    """The external effect happened, but local bookkeeping did not finish."""


class IdempotencyConflict(RuntimeError):
    """The same idempotency key was reused for a different request fingerprint."""


class PermanentError(RuntimeError):
    """An error that retry should not repeat."""


class TransientError(RuntimeError):
    """An error that may succeed after a bounded retry."""


@dataclass(frozen=True)
class RequestResult:
    response: dict[str, object]
    replayed: bool


def canonical_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(data: object) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def request_fingerprint(customer_id: str, amount_cents: int) -> str:
    return sha256_hex({"amount_cents": amount_cents, "customer_id": customer_id, "operation": "charge"})


def stable_order_id(idempotency_key: str) -> str:
    return "ord_" + hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:12]


def stable_event_id(idempotency_key: str, fingerprint: str) -> str:
    material = {"idempotency_key": idempotency_key, "fingerprint": fingerprint, "event": "charge.requested"}
    return "evt_" + sha256_hex(material)[:16]


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


def init_app_db(path: Path) -> None:
    with _connect(path) as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                request_id TEXT PRIMARY KEY,
                amount_cents INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS idempotency_requests (
                idempotency_key TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                customer_id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS outbox (
                event_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                sent_at INTEGER
            );
            """
        )


def init_gateway_db(path: Path) -> None:
    with _connect(path) as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS non_idempotent_effects (
                delivery_id TEXT PRIMARY KEY,
                logical_key TEXT NOT NULL,
                amount_cents INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS idempotent_effects (
                event_id TEXT PRIMARY KEY,
                payload_hash TEXT NOT NULL,
                amount_cents INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS idempotent_deliveries (
                delivery_no INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                applied_new INTEGER NOT NULL
            );
            """
        )


def reset_databases(app_db: Path, gateway_db: Path) -> None:
    for path in (app_db, gateway_db):
        path.unlink(missing_ok=True)
    init_app_db(app_db)
    init_gateway_db(gateway_db)


def apply_non_idempotent_effect(gateway_db: Path, delivery_id: str, logical_key: str, amount_cents: int) -> None:
    if amount_cents <= 0:
        raise PermanentError("amount_cents must be positive")
    with _connect(gateway_db) as con:
        con.execute(
            "INSERT INTO non_idempotent_effects(delivery_id, logical_key, amount_cents) VALUES (?, ?, ?)",
            (delivery_id, logical_key, amount_cents),
        )


def apply_idempotent_effect(gateway_db: Path, event_id: str, payload: dict[str, object]) -> bool:
    amount_cents = int(payload["amount_cents"])
    if amount_cents <= 0:
        raise PermanentError("amount_cents must be positive")
    payload_hash = sha256_hex(payload)
    con = _connect(gateway_db)
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT payload_hash FROM idempotent_effects WHERE event_id = ?", (event_id,)).fetchone()
        if row is None:
            con.execute(
                "INSERT INTO idempotent_effects(event_id, payload_hash, amount_cents) VALUES (?, ?, ?)",
                (event_id, payload_hash, amount_cents),
            )
            applied_new = 1
        elif row["payload_hash"] != payload_hash:
            raise IdempotencyConflict(f"event_id {event_id} reused with different payload")
        else:
            applied_new = 0
        con.execute(
            "INSERT INTO idempotent_deliveries(event_id, applied_new) VALUES (?, ?)",
            (event_id, applied_new),
        )
        con.commit()
        return bool(applied_new)
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def naive_charge_request(
    app_db: Path,
    gateway_db: Path,
    *,
    request_id: str,
    attempt_id: str,
    amount_cents: int,
    crash_after_effect: bool = False,
) -> None:
    apply_non_idempotent_effect(
        gateway_db,
        delivery_id=f"naive-{request_id}-{attempt_id}",
        logical_key=request_id,
        amount_cents=amount_cents,
    )
    if crash_after_effect:
        raise CrashAfterSideEffect("crashed after gateway effect and before local receipt")
    with _connect(app_db) as con:
        con.execute(
            "INSERT OR REPLACE INTO receipts(request_id, amount_cents) VALUES (?, ?)",
            (request_id, amount_cents),
        )


def create_order_with_idempotency(
    app_db: Path,
    *,
    idempotency_key: str,
    customer_id: str,
    amount_cents: int,
) -> RequestResult:
    if amount_cents <= 0:
        raise PermanentError("amount_cents must be positive")
    fingerprint = request_fingerprint(customer_id, amount_cents)
    con = _connect(app_db)
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            "SELECT fingerprint, response_json FROM idempotency_requests WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if row is not None:
            if row["fingerprint"] != fingerprint:
                raise IdempotencyConflict("same idempotency key used for a different request payload")
            con.commit()
            return RequestResult(json.loads(row["response_json"]), replayed=True)

        order_id = stable_order_id(idempotency_key)
        event_id = stable_event_id(idempotency_key, fingerprint)
        response = {
            "schema_version": SCHEMA_VERSION,
            "order_id": order_id,
            "event_id": event_id,
            "status": "accepted",
            "amount_cents": amount_cents,
        }
        payload = {
            "schema_version": SCHEMA_VERSION,
            "order_id": order_id,
            "customer_id": customer_id,
            "amount_cents": amount_cents,
        }
        con.execute(
            "INSERT INTO orders(order_id, idempotency_key, customer_id, amount_cents) VALUES (?, ?, ?, ?)",
            (order_id, idempotency_key, customer_id, amount_cents),
        )
        con.execute(
            "INSERT INTO outbox(event_id, idempotency_key, kind, payload_json, sent_at) VALUES (?, ?, ?, ?, NULL)",
            (event_id, idempotency_key, "charge.requested", canonical_json(payload)),
        )
        con.execute(
            "INSERT INTO idempotency_requests(idempotency_key, fingerprint, response_json) VALUES (?, ?, ?)",
            (idempotency_key, fingerprint, canonical_json(response)),
        )
        con.commit()
        return RequestResult(response, replayed=False)
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _next_non_idempotent_delivery_id(gateway_db: Path, event_id: str) -> str:
    with _connect(gateway_db) as con:
        count = con.execute(
            "SELECT COUNT(*) AS n FROM non_idempotent_effects WHERE logical_key = ?", (event_id,)
        ).fetchone()["n"]
    return f"delivery-{event_id}-{count + 1}"


def dispatch_one_outbox(
    app_db: Path,
    gateway_db: Path,
    *,
    receiver_mode: str,
    crash_after_send: bool = False,
) -> str | None:
    with _connect(app_db) as con:
        row = con.execute(
            "SELECT event_id, payload_json FROM outbox WHERE sent_at IS NULL ORDER BY event_id LIMIT 1"
        ).fetchone()
    if row is None:
        return None
    event_id = str(row["event_id"])
    payload = json.loads(row["payload_json"])
    if receiver_mode == "non_idempotent":
        apply_non_idempotent_effect(
            gateway_db,
            delivery_id=_next_non_idempotent_delivery_id(gateway_db, event_id),
            logical_key=event_id,
            amount_cents=int(payload["amount_cents"]),
        )
    elif receiver_mode == "idempotent":
        apply_idempotent_effect(gateway_db, event_id, payload)
    else:
        raise ValueError("receiver_mode must be non_idempotent or idempotent")
    if crash_after_send:
        raise CrashAfterSideEffect("dispatcher crashed after sending and before marking outbox sent")
    with _connect(app_db) as con:
        con.execute("UPDATE outbox SET sent_at = 1 WHERE event_id = ?", (event_id,))
    return event_id


def count_app_rows(app_db: Path) -> dict[str, int]:
    with _connect(app_db) as con:
        return {
            "receipts": con.execute("SELECT COUNT(*) AS n FROM receipts").fetchone()["n"],
            "orders": con.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"],
            "idempotency_requests": con.execute("SELECT COUNT(*) AS n FROM idempotency_requests").fetchone()["n"],
            "outbox_total": con.execute("SELECT COUNT(*) AS n FROM outbox").fetchone()["n"],
            "outbox_unsent": con.execute("SELECT COUNT(*) AS n FROM outbox WHERE sent_at IS NULL").fetchone()["n"],
            "outbox_sent": con.execute("SELECT COUNT(*) AS n FROM outbox WHERE sent_at IS NOT NULL").fetchone()["n"],
        }


def count_gateway_rows(gateway_db: Path) -> dict[str, int]:
    with _connect(gateway_db) as con:
        return {
            "non_idempotent_effects": con.execute(
                "SELECT COUNT(*) AS n FROM non_idempotent_effects"
            ).fetchone()["n"],
            "idempotent_effects": con.execute("SELECT COUNT(*) AS n FROM idempotent_effects").fetchone()["n"],
            "idempotent_deliveries": con.execute(
                "SELECT COUNT(*) AS n FROM idempotent_deliveries"
            ).fetchone()["n"],
            "idempotent_duplicate_deliveries": con.execute(
                "SELECT COUNT(*) AS n FROM idempotent_deliveries WHERE applied_new = 0"
            ).fetchone()["n"],
        }


def retry_with_policy(
    operation: Callable[[], T],
    *,
    max_attempts: int = 3,
    sleep_seconds: float = 0.0,
) -> tuple[T, int]:
    attempts = 0
    while True:
        attempts += 1
        try:
            return operation(), attempts
        except PermanentError:
            raise
        except TransientError:
            if attempts >= max_attempts:
                raise
            if sleep_seconds:
                time.sleep(sleep_seconds)


class FailsOnceThenSucceeds:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        if self.calls == 1:
            raise TransientError("temporary unavailable")
        return "ok"


class AlwaysPermanentFailure:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        raise PermanentError("invalid request")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init-app", type=Path)
    parser.add_argument("--init-gateway", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.init_app:
        init_app_db(args.init_app)
    if args.init_gateway:
        init_gateway_db(args.init_gateway)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IdempotencyConflict as exc:
        print(f"idempotency conflict: {exc}", file=sys.stderr)
        raise SystemExit(RC_IDEMPOTENCY_CONFLICT)
    except PermanentError as exc:
        print(f"permanent error: {exc}", file=sys.stderr)
        raise SystemExit(RC_PERMANENT_ERROR)
