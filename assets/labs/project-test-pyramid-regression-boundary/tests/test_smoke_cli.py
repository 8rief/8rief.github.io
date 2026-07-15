import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "test_pyramid_demo.py"


class SmokeCliTests(unittest.TestCase):
    def test_cli_success_path_prints_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "summary.json"
            log = Path(tmp) / "events.jsonl"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(ROOT / "data" / "orders.csv"),
                    "--output",
                    str(out),
                    "--log",
                    str(log),
                    "--golden",
                    str(ROOT / "fixtures" / "golden_summary.json"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PIPELINE_OK", result.stdout)
            self.assertTrue(out.exists())
            self.assertTrue(log.exists())


if __name__ == "__main__":
    unittest.main()
