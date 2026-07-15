#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import server  # noqa: E402


class ServerStateTests(unittest.TestCase):
    def test_record_visit_persists_and_trims_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for idx in range(25):
                state = server.record_visit(f"visit-{idx}", root)
            self.assertEqual(state["visits"], 25)
            self.assertEqual(len(state["events"]), 20)
            loaded = server.load_state(root)
            self.assertEqual(loaded["visits"], 25)
            self.assertEqual(loaded["events"][-1]["label"], "visit-24")

    def test_empty_label_becomes_anonymous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = server.record_visit("   ", root)
            self.assertEqual(state["events"][-1]["label"], "anonymous")


if __name__ == "__main__":
    unittest.main()
