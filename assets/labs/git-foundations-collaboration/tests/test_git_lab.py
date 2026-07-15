from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import git_lab  # noqa: E402


class GitLabScenarioTests(unittest.TestCase):
    def test_full_scenario_writes_reports_and_expected_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observations = git_lab.run_scenario(root / "workspace", root / "reports")
            report = (root / "reports" / "git_foundations_report.md").read_text(encoding="utf-8")
            loaded = json.loads((root / "reports" / "observations.json").read_text(encoding="utf-8"))
            self.assertIn("git version", observations["git_version"])
            self.assertEqual(observations["working_tree_index_commit"]["head_type"], "commit")
            self.assertEqual(observations["working_tree_index_commit"]["tree_type"], "tree")
            self.assertIn("README.md", observations["working_tree_index_commit"]["tree_entries"])
            self.assertIn("+owner: team-a", observations["diff_and_patch"]["staged_diff_excerpt"])
            self.assertNotEqual(observations["merge_conflict"]["merge_returncode"], 0)
            self.assertTrue(observations["merge_conflict"]["conflict_markers_seen"])
            self.assertIn("review: completed", observations["merge_conflict"]["resolved_file"])
            self.assertTrue(observations["rebase_boundary"]["hash_changed_by_rebase"])
            self.assertIn("v0.1.0", observations["remote_collaboration"]["tags"])
            self.assertEqual(
                observations["remote_collaboration"]["local_after_pull"],
                observations["remote_collaboration"]["origin_main_after_fetch"],
            )
            self.assertEqual(observations["final_status"], [])
            self.assertIn("Merge conflict", report)
            self.assertEqual(loaded["remote_collaboration"]["tags"], ["v0.1.0"])

    def test_short_result_truncates_stdout(self) -> None:
        result = git_lab.CommandResult(argv=["x"], cwd="/tmp", returncode=0, stdout="a" * 20, stderr="")
        self.assertEqual(git_lab.short(result, limit=5)["stdout"], "aaaaa")


if __name__ == "__main__":
    unittest.main()
