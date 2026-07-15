from __future__ import annotations

import subprocess
import sys
import time
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from versioned_counter import (  # noqa: E402
    FileLock,
    LockTimeout,
    StateError,
    VersionConflict,
    atomic_write_state,
    compare_and_increment,
    increment_locked,
    initial_state,
    read_state,
)


class VersionedCounterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="counter-test-")
        self.root = Path(self.temporary.name)
        self.state = self.root / "counter.json"
        self.lock = self.root / "counter.lock"
        atomic_write_state(self.state, initial_state())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_atomic_round_trip_is_canonical(self) -> None:
        atomic_write_state(self.state, {"value": 2, "version": 2, "schema_version": 1})
        self.assertEqual(read_state(self.state)["value"], 2)
        self.assertEqual(
            self.state.read_text(encoding="utf-8"),
            '{"schema_version":1,"value":2,"version":2}\n',
        )

    def test_invalid_counter_invariant_is_rejected(self) -> None:
        self.state.write_text('{"schema_version":1,"version":2,"value":1}\n', encoding="utf-8")
        with self.assertRaises(StateError):
            read_state(self.state)

    def test_stable_lock_inode_survives_state_replacement(self) -> None:
        with FileLock(self.lock, 0.2):
            lock_inode = self.lock.stat().st_ino
            old_state_inode = self.state.stat().st_ino
            atomic_write_state(self.state, {"schema_version": 1, "version": 1, "value": 1})
        self.assertEqual(self.lock.stat().st_ino, lock_inode)
        self.assertNotEqual(self.state.stat().st_ino, old_state_inode)

    def test_compare_and_increment_detects_stale_version(self) -> None:
        first = compare_and_increment(self.state, self.lock, expected_version=0, timeout_seconds=0.2)
        self.assertEqual(first["value"], 1)
        with self.assertRaises(VersionConflict):
            compare_and_increment(self.state, self.lock, expected_version=0, timeout_seconds=0.2)

    def test_lock_timeout_is_bounded(self) -> None:
        ready = self.root / "holder.ready"
        holder = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "src" / "versioned_counter.py"),
                "hold-lock",
                "--lock",
                str(self.lock),
                "--ready",
                str(ready),
                "--hold-ms",
                "300",
            ]
        )
        for _ in range(100):
            if ready.exists():
                break
            time.sleep(0.01)
        self.assertTrue(ready.exists())
        with self.assertRaises(LockTimeout):
            increment_locked(self.state, self.lock, timeout_seconds=0.03)
        self.assertEqual(holder.wait(timeout=3), 0)


if __name__ == "__main__":
    unittest.main()
