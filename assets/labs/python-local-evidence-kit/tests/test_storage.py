from __future__ import annotations

import csv

from local_evidence.scanner import build_manifest
from local_evidence.storage import read_manifest_json, write_manifest_csv, write_manifest_json


def test_manifest_json_and_csv_exports(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "hello.txt").write_text("hello", encoding="utf-8")
    manifest = build_manifest(data_dir)

    json_path = tmp_path / "out" / "manifest.json"
    csv_path = tmp_path / "out" / "manifest.csv"
    write_manifest_json(manifest, json_path)
    write_manifest_csv(manifest, csv_path)

    payload = read_manifest_json(json_path)
    assert payload["summary"] == {"file_count": 1, "total_bytes": 5}

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["path"] == "hello.txt"
    assert rows[0]["size_bytes"] == "5"
