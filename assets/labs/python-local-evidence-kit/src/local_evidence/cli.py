from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .logging_utils import configure_logging
from .scanner import build_manifest
from .storage import read_manifest_json, write_manifest_csv, write_manifest_json

app = typer.Typer(help="Build and inspect local file evidence manifests.")


@app.command()
def scan(
    path: Path = typer.Argument(..., help="Directory to scan."),
    json_output: Optional[Path] = typer.Option(None, "--json", help="Write manifest JSON."),
    csv_output: Optional[Path] = typer.Option(None, "--csv", help="Write manifest CSV."),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level."),
) -> None:
    """Scan a directory and optionally export JSON/CSV reports."""
    configure_logging(log_level)
    manifest = build_manifest(path)
    if json_output is not None:
        write_manifest_json(manifest, json_output)
    if csv_output is not None:
        write_manifest_csv(manifest, csv_output)
    typer.echo(
        f"scanned root={manifest.root_name} files={manifest.summary.file_count} "
        f"bytes={manifest.summary.total_bytes}"
    )


@app.command()
def summary(manifest_json: Path = typer.Argument(..., help="Manifest JSON produced by scan.")) -> None:
    """Print a compact summary from a saved manifest."""
    payload = read_manifest_json(manifest_json)
    summary_payload = payload["summary"]
    typer.echo(
        f"manifest root={payload['root_name']} files={summary_payload['file_count']} "
        f"bytes={summary_payload['total_bytes']}"
    )


if __name__ == "__main__":
    app()
