from __future__ import annotations

from typer.testing import CliRunner

from local_evidence.cli import app


def test_cli_scan_and_summary(tmp_path):
    runner = CliRunner()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "a.txt").write_text("A", encoding="utf-8")
    manifest_json = tmp_path / "manifest.json"
    manifest_csv = tmp_path / "manifest.csv"

    scan_result = runner.invoke(app, ["scan", str(data_dir), "--json", str(manifest_json), "--csv", str(manifest_csv)])
    assert scan_result.exit_code == 0, scan_result.output
    assert "files=1" in scan_result.output
    assert manifest_json.exists()
    assert manifest_csv.exists()

    summary_result = runner.invoke(app, ["summary", str(manifest_json)])
    assert summary_result.exit_code == 0, summary_result.output
    assert "manifest root=data files=1 bytes=1" in summary_result.output
