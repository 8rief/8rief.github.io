from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import demo_app  # noqa: E402


class ConfigTests(unittest.TestCase):
    def test_precedence_and_sources(self) -> None:
        resolved = demo_app.resolve_config(
            ROOT / "config" / "defaults.json",
            ROOT / "config" / "development.json",
            {
                "DEMO_HOST": "192.0.2.10",
                "DEMO_PORT": "18080",
            },
            {"port": 19090, "log_level": "DEBUG"},
        )
        self.assertEqual(resolved.config.service_name, "config-log-demo")
        self.assertEqual(resolved.config.host, "192.0.2.10")
        self.assertEqual(resolved.config.port, 19090)
        self.assertEqual(resolved.config.log_level, "DEBUG")
        self.assertEqual(resolved.sources["service_name"], "defaults")
        self.assertEqual(resolved.sources["output_dir"], "file")
        self.assertEqual(resolved.sources["host"], "env")
        self.assertEqual(resolved.sources["port"], "cli")

    def test_unknown_key_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"unexpected": true}\n', encoding="utf-8")
            with self.assertRaisesRegex(demo_app.ConfigError, "unknown keys: unexpected"):
                demo_app.load_json_object(path, "config")

    def test_invalid_port_is_rejected(self) -> None:
        raw = json.loads((ROOT / "config" / "defaults.json").read_text(encoding="utf-8"))
        raw["port"] = "not-an-integer"
        with self.assertRaisesRegex(demo_app.ConfigError, "port must be an integer"):
            demo_app.validate_config(raw)

    def test_atomic_json_write_leaves_complete_document(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            demo_app.atomic_write_json(path, {"status": "ok"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"status": "ok"})
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
