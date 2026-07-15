from __future__ import annotations

from hashlib import sha256

import pytest

from local_evidence.scanner import ScanBoundaryError, build_manifest


def test_build_manifest_is_deterministic(tmp_path):
    (tmp_path / "b.txt").write_text("beta\n", encoding="utf-8")
    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8")

    manifest = build_manifest(tmp_path)

    assert [entry.path for entry in manifest.entries] == ["a.txt", "b.txt"]
    assert manifest.summary.file_count == 2
    assert manifest.summary.total_bytes == len("alpha\n") + len("beta\n")
    assert manifest.entries[0].sha256 == sha256(b"alpha\n").hexdigest()


def test_scan_rejects_file_root(tmp_path):
    file_path = tmp_path / "one.txt"
    file_path.write_text("one", encoding="utf-8")

    with pytest.raises(ScanBoundaryError):
        build_manifest(file_path)
