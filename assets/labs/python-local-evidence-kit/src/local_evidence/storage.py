from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import Manifest


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def write_manifest_json(manifest: Manifest, path: Path | str) -> None:
    destination = Path(path)
    content = json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    _atomic_write_text(destination, content + "\n")


def write_manifest_csv(manifest: Manifest, path: Path | str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_name(destination.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "size_bytes", "sha256"])
        writer.writeheader()
        for entry in manifest.entries:
            writer.writerow(entry.to_dict())
    tmp.replace(destination)


def read_manifest_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
