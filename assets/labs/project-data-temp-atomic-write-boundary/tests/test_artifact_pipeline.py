from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import artifact_pipeline as pipeline  # noqa: E402


class ArtifactPipelineTests(unittest.TestCase):
    def test_summary_is_deterministic(self) -> None:
        orders, _ = pipeline.load_orders(ROOT / "fixtures" / "orders.jsonl")
        config, _ = pipeline.load_config(ROOT / "config" / "pipeline.json")
        expected = {
            "schema_version": 1,
            "currency": "CNY",
            "included_statuses": ["paid", "pending"],
            "selected_order_count": 3,
            "total_amount_cents": 4500,
            "count_by_status": {"paid": 2, "pending": 1},
        }
        self.assertEqual(pipeline.build_summary(orders, config), expected)

    def test_forced_failure_preserves_old_output_and_cleans_temp(self) -> None:
        with TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            output = root / "output" / "summary.json"
            manifest = root / "output" / "manifest.json"
            output.parent.mkdir()
            old_bytes = b'{"sentinel":"old-output"}\n'
            output.write_bytes(old_bytes)
            with self.assertRaises(pipeline.ForcedBeforeReplace):
                pipeline.run_pipeline(
                    ROOT / "fixtures" / "orders.jsonl",
                    ROOT / "config" / "pipeline.json",
                    output,
                    manifest,
                    fail_before_replace=True,
                )
            self.assertEqual(output.read_bytes(), old_bytes)
            self.assertFalse(manifest.exists())
            self.assertEqual(list(output.parent.glob(".*.tmp")), [])

    def test_successful_reruns_are_byte_identical(self) -> None:
        with TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            output = root / "output" / "summary.json"
            manifest = root / "output" / "manifest.json"
            args = (
                ROOT / "fixtures" / "orders.jsonl",
                ROOT / "config" / "pipeline.json",
                output,
                manifest,
            )
            first = pipeline.run_pipeline(*args)
            first_output = output.read_bytes()
            first_manifest = manifest.read_bytes()
            second = pipeline.run_pipeline(*args)
            self.assertEqual(output.read_bytes(), first_output)
            self.assertEqual(manifest.read_bytes(), first_manifest)
            self.assertEqual(first, second)
            self.assertEqual(first["output_sha256"], pipeline.sha256_bytes(first_output))

    def test_duplicate_order_id_is_rejected(self) -> None:
        with TemporaryDirectory(dir="/tmp") as tmp:
            path = Path(tmp) / "duplicate.jsonl"
            path.write_text(
                '{"order_id":"A1","status":"paid","amount_cents":1}\n'
                '{"order_id":"A1","status":"pending","amount_cents":2}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(pipeline.PipelineError, "duplicate order_id"):
                pipeline.load_orders(path)

    def test_non_utf8_input_is_rejected_at_boundary(self) -> None:
        with TemporaryDirectory(dir="/tmp") as tmp:
            path = Path(tmp) / "invalid.jsonl"
            path.write_bytes(b"\xff\xfe\x00")
            with self.assertRaisesRegex(pipeline.PipelineError, "valid UTF-8"):
                pipeline.load_orders(path)


if __name__ == "__main__":
    unittest.main()
