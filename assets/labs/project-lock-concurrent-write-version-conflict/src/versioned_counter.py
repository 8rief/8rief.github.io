#!/usr/bin/env python3
"""A versioned JSON counter with unsafe, locked, and optimistic writers."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import tempfile
import time
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any


RC_CONFLICT = 73
RC_LOCK_TIMEOUT = 75
SCHEMA_VERSION = 1


class StateError(ValueError):
    """The on-disk state does not satisfy the counter schema."""


class VersionConflict(RuntimeError):
    """The expected version is no longer current."""


class LockTimeout(TimeoutError):
    """The lock could not be acquired within the configured bound."""


def initial_state() -> dict[str, int]:
    return {"schema_version": SCHEMA_VERSION, "version": 0, "value": 0}


def _validate_state(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "version", "value"}:
        raise StateError("state must contain exactly schema_version, version, and value")
    if any(type(raw[key]) is not int for key in raw):
        raise StateError("all state fields must be integers")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise StateError(f"unsupported schema_version: {raw['schema_version']}")
    if raw["version"] < 0 or raw["value"] < 0:
        raise StateError("version and value must be non-negative")
    if raw["version"] != raw["value"]:
        raise StateError("counter invariant requires version == value")
    return {key: raw[key] for key in ("schema_version", "version", "value")}


def read_state(path: Path) -> dict[str, int]:
    try:
        text = path.read_text(encoding="utf-8")
        raw = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError(f"cannot read valid UTF-8 JSON state: {exc}") from exc
    return _validate_state(raw)


def _canonical_bytes(state: dict[str, int]) -> bytes:
    checked = _validate_state(state)
    return (json.dumps(checked, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def atomic_write_state(path: Path, state: dict[str, int]) -> None:
    """Atomically publish one state and request file/directory persistence."""
    payload = _canonical_bytes(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, candidate_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    candidate = Path(candidate_name)
    try:
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(candidate, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        candidate.unlink(missing_ok=True)


class FileLock(AbstractContextManager["FileLock"]):
    """A bounded advisory exclusive lock on a stable, separate lock file."""

    def __init__(self, path: Path, timeout_seconds: float, poll_seconds: float = 0.01):
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        if poll_seconds <= 0:
            raise ValueError("poll_seconds must be positive")
        self.path = path
        self.timeout_seconds = timeout_seconds
        self.poll_seconds = poll_seconds
        self._stream: Any = None

    def __enter__(self) -> "FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self.path.open("a+b")
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            try:
                fcntl.flock(self._stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    self._stream.close()
                    self._stream = None
                    raise LockTimeout(f"timed out acquiring {self.path.name}")
                time.sleep(min(self.poll_seconds, max(0.0, deadline - time.monotonic())))

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self._stream is not None:
            fcntl.flock(self._stream.fileno(), fcntl.LOCK_UN)
            self._stream.close()
            self._stream = None


def _next_state(current: dict[str, int]) -> dict[str, int]:
    return {
        "schema_version": SCHEMA_VERSION,
        "version": current["version"] + 1,
        "value": current["value"] + 1,
    }


def increment_locked(
    state_path: Path,
    lock_path: Path,
    *,
    timeout_seconds: float,
    hold_seconds: float = 0.0,
) -> dict[str, int]:
    with FileLock(lock_path, timeout_seconds):
        current = read_state(state_path)
        if hold_seconds:
            time.sleep(hold_seconds)
        updated = _next_state(current)
        atomic_write_state(state_path, updated)
        return updated


def compare_and_increment(
    state_path: Path,
    lock_path: Path,
    *,
    expected_version: int,
    timeout_seconds: float,
) -> dict[str, int]:
    """Perform a local compare-and-swap using a short advisory lock."""
    with FileLock(lock_path, timeout_seconds):
        current = read_state(state_path)
        if current["version"] != expected_version:
            raise VersionConflict(
                f"expected version {expected_version}, current version {current['version']}"
            )
        updated = _next_state(current)
        atomic_write_state(state_path, updated)
        return updated


def _barrier(ready_dir: Path, worker_id: str, participants: int, timeout_seconds: float = 5.0) -> None:
    ready_dir.mkdir(parents=True, exist_ok=True)
    (ready_dir / f"ready-{worker_id}.marker").write_text("ready\n", encoding="utf-8")
    deadline = time.monotonic() + timeout_seconds
    while len(list(ready_dir.glob("ready-*.marker"))) < participants:
        if time.monotonic() >= deadline:
            raise TimeoutError("worker barrier timed out")
        time.sleep(0.01)


def _positive_milliseconds(value: str) -> float:
    milliseconds = int(value)
    if milliseconds < 0:
        raise argparse.ArgumentTypeError("milliseconds must be non-negative")
    return milliseconds / 1000.0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    unsafe = subparsers.add_parser("unsafe", help="race one unprotected read-modify-replace")
    unsafe.add_argument("--state", type=Path, required=True)
    unsafe.add_argument("--ready-dir", type=Path, required=True)
    unsafe.add_argument("--worker-id", required=True)
    unsafe.add_argument("--participants", type=int, default=2)
    unsafe.add_argument("--delay-ms", type=_positive_milliseconds, default=0.0)

    locked = subparsers.add_parser("locked", help="increment under one complete critical section")
    locked.add_argument("--state", type=Path, required=True)
    locked.add_argument("--lock", type=Path, required=True)
    locked.add_argument("--hold-ms", type=_positive_milliseconds, default=0.0)
    locked.add_argument("--timeout-ms", type=_positive_milliseconds, default=_positive_milliseconds("1000"))

    cas = subparsers.add_parser("cas", help="compare expected version and increment")
    cas.add_argument("--state", type=Path, required=True)
    cas.add_argument("--lock", type=Path, required=True)
    cas.add_argument("--expected-version", type=int, required=True)
    cas.add_argument("--ready-dir", type=Path)
    cas.add_argument("--worker-id")
    cas.add_argument("--participants", type=int, default=2)
    cas.add_argument("--delay-ms", type=_positive_milliseconds, default=0.0)
    cas.add_argument("--timeout-ms", type=_positive_milliseconds, default=_positive_milliseconds("1000"))

    hold = subparsers.add_parser("hold-lock", help="hold a lock for timeout experiments")
    hold.add_argument("--lock", type=Path, required=True)
    hold.add_argument("--ready", type=Path, required=True)
    hold.add_argument("--hold-ms", type=_positive_milliseconds, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "unsafe":
            current = read_state(args.state)
            proposed = _next_state(current)
            _barrier(args.ready_dir, args.worker_id, args.participants)
            time.sleep(args.delay_ms)
            atomic_write_state(args.state, proposed)
            print(json.dumps(proposed, sort_keys=True))
        elif args.command == "locked":
            result = increment_locked(
                args.state,
                args.lock,
                timeout_seconds=args.timeout_ms,
                hold_seconds=args.hold_ms,
            )
            print(json.dumps(result, sort_keys=True))
        elif args.command == "cas":
            if args.ready_dir is not None:
                if not args.worker_id:
                    raise ValueError("--worker-id is required with --ready-dir")
                _barrier(args.ready_dir, args.worker_id, args.participants)
            time.sleep(args.delay_ms)
            result = compare_and_increment(
                args.state,
                args.lock,
                expected_version=args.expected_version,
                timeout_seconds=args.timeout_ms,
            )
            print(json.dumps(result, sort_keys=True))
        elif args.command == "hold-lock":
            with FileLock(args.lock, 1.0):
                args.ready.parent.mkdir(parents=True, exist_ok=True)
                args.ready.write_text("locked\n", encoding="utf-8")
                time.sleep(args.hold_ms)
        return 0
    except VersionConflict as exc:
        print(f"version conflict: {exc}", file=sys.stderr)
        return RC_CONFLICT
    except LockTimeout as exc:
        print(f"lock timeout: {exc}", file=sys.stderr)
        return RC_LOCK_TIMEOUT


if __name__ == "__main__":
    raise SystemExit(main())
