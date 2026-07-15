from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FileEntry:
    """One file entry in a manifest."""

    path: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ManifestSummary:
    """Small aggregate that is safe to print in a CLI or return from an API."""

    file_count: int
    total_bytes: int

    def to_dict(self) -> dict[str, int]:
        return {
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
        }


@dataclass(frozen=True)
class Manifest:
    """A deterministic manifest for all regular files under one root."""

    root_name: str
    entries: tuple[FileEntry, ...]

    @property
    def summary(self) -> ManifestSummary:
        return ManifestSummary(
            file_count=len(self.entries),
            total_bytes=sum(entry.size_bytes for entry in self.entries),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_name": self.root_name,
            "summary": self.summary.to_dict(),
            "entries": [entry.to_dict() for entry in self.entries],
        }
