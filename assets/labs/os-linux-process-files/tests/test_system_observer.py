from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import system_observer  # noqa: E402


class SystemObserverTests(unittest.TestCase):
    def test_prepare_workspace_creates_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = system_observer.prepare_workspace(Path(tmp))
            self.assertTrue((paths["files"] / "alpha.txt").exists())
            self.assertIn("ERROR timeout", (paths["logs"] / "events.log").read_text(encoding="utf-8"))

    def test_file_record_has_inode_mode_and_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sample.txt"
            target.write_text("hello\n", encoding="utf-8")
            record = system_observer.file_record(target)
            self.assertEqual(record["file_type"], "regular")
            self.assertGreater(record["inode"], 0)
            self.assertGreater(record["size_bytes"], 0)
            self.assertTrue(record["mode_symbolic"].startswith("-"))

    def test_descriptor_demo_writes_one_file_from_two_descriptors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = system_observer.descriptor_demo(Path(tmp))
            self.assertEqual(
                result["content"],
                ["written through original fd", "written through duplicated fd"],
            )

    def test_environment_child_receives_explicit_marker(self) -> None:
        result = system_observer.environment_observation()
        self.assertEqual(result["child_stdout"], "visible-to-child")
        self.assertEqual(result["child_returncode"], 0)
        self.assertFalse(result["parent_has_marker_before_spawn"])

    def test_permission_demo_reflects_umask(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = system_observer.permission_observation(Path(tmp))
            self.assertEqual(result["result_mode"], "0o640")

    def test_pipeline_counts_log_levels_and_users(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = system_observer.prepare_workspace(Path(tmp))
            result = system_observer.pipeline_observation(paths["logs"] / "events.log")
            self.assertIn("      3 INFO", result["level_counts"])
            self.assertIn("      2 WARN", result["level_counts"])
            self.assertIn("      1 ERROR", result["level_counts"])
            self.assertIn("      2 user=alice", result["user_counts"])
            self.assertIn("      3 user=bob", result["user_counts"])

    def test_collect_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observations = system_observer.collect(root / "workspace", root / "reports")
            loaded = json.loads((root / "reports" / "observations.json").read_text(encoding="utf-8"))
            self.assertEqual(loaded["permissions"]["result_mode"], "0o640")
            self.assertIn("filesystem", observations)
            self.assertIn("Process snapshot", (root / "reports" / "system_observer_report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
