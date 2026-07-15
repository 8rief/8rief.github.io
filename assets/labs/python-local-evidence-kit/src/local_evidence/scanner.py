from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from .models import FileEntry, Manifest


class ScanBoundaryError(ValueError):
    """Raised when a requested scan root cannot be treated as a directory."""


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_regular_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def build_manifest(root: Path | str) -> Manifest:
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"scan root does not exist: {root_path}")
    if not root_path.is_dir():
        raise ScanBoundaryError(f"scan root is not a directory: {root_path}")

    entries: list[FileEntry] = []
    for path in iter_regular_files(root_path):
        relative = path.relative_to(root_path).as_posix()
        entries.append(
            FileEntry(
                path=relative,
                size_bytes=path.stat().st_size,
                sha256=hash_file(path),
            )
        )
    return Manifest(root_name=root_path.name, entries=tuple(entries))
