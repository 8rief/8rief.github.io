from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workflow_kit.config import ProjectConfig
from workflow_kit.domain import Task, next_task_id, summarize
from workflow_kit.layout import create_layout
from workflow_kit.storage import load_state, save_state, state_from_tasks, tasks_from_state


class WorkflowKitTests(unittest.TestCase):
    def test_domain_validation_and_summary(self) -> None:
        task = Task(task_id=1, title="write README", owner="qiao")
        self.assertEqual(task.status, "todo")
        with self.assertRaises(ValueError):
            Task(task_id=2, title=" ")
        self.assertEqual(next_task_id([task]), 2)
        self.assertEqual(summarize([task])["todo"], 1)

    def test_layout_creates_expected_directories(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "demo"
            create_layout(ProjectConfig(root=root, name="demo"))
            for folder in ["src", "tests", "docs", "scripts", "reports", "config", "data"]:
                self.assertTrue((root / folder).is_dir())
            self.assertTrue((root / "README.md").exists())
            self.assertIn(".env", (root / ".gitignore").read_text(encoding="utf-8"))

    def test_storage_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "data" / "tasks.json"
            tasks = [Task(task_id=1, title="slice requirement", status="doing")]
            save_state(path, state_from_tasks("demo", tasks))
            loaded = tasks_from_state(load_state(path))
            self.assertEqual(loaded[0].title, "slice requirement")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 1)

    def test_cli_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "demo"
            env = {"PYTHONPATH": str(Path.cwd() / "src")}
            commands = [
                [sys.executable, "-m", "workflow_kit.cli", "init", "--root", str(root), "--name", "demo"],
                [sys.executable, "-m", "workflow_kit.cli", "add", "--root", str(root), "--owner", "dev", "design module boundary"],
                [sys.executable, "-m", "workflow_kit.cli", "add", "--root", str(root), "--status", "doing", "write tests"],
                [sys.executable, "-m", "workflow_kit.cli", "done", "--root", str(root), "1"],
                [sys.executable, "-m", "workflow_kit.cli", "report", "--root", str(root)],
            ]
            for command in commands:
                subprocess.run(command, cwd=Path.cwd(), env=env, text=True, capture_output=True, check=True)
            listing = subprocess.run([sys.executable, "-m", "workflow_kit.cli", "list", "--root", str(root)], cwd=Path.cwd(), env=env, text=True, capture_output=True, check=True).stdout
            self.assertIn("done\tdev\tdesign module boundary", listing)
            self.assertTrue((root / "reports" / "summary.md").exists())


if __name__ == "__main__":
    unittest.main()
