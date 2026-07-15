#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "reports" / "metrics.json"


class SystemsLabTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metrics = json.loads(METRICS.read_text(encoding="utf-8"))

    def test_core_contract(self) -> None:
        m = self.metrics
        self.assertEqual(m["systems_os_status"], "ok")
        self.assertEqual(m["data_uint32_size"], 4)
        self.assertTrue(m["memory_stack_heap_distinct"])
        self.assertEqual(m["process_child_exit_code"], 42)
        self.assertEqual(m["fd_file_bytes_written"], m["fd_file_bytes_read"])
        self.assertGreaterEqual(m["vm_page_size"], 4096)
        self.assertTrue(m["vm_cow_parent_unchanged"])
        self.assertLess(m["thread_controlled_race_actual"], m["thread_controlled_race_expected"])
        self.assertTrue(m["thread_mutex_correct"])
        self.assertEqual(m["signal_ipc_message"], "signal-ok")
        self.assertTrue(m["cache_sums_equal"])
        self.assertGreater(m["cache_row_major_ns"], 0)
        self.assertGreater(m["cache_column_major_ns"], 0)


if __name__ == "__main__":
    unittest.main()
