from __future__ import annotations

from pathlib import Path


class PathBoundaryError(ValueError):
    """Raised when a requested path escapes the configured document root."""


def safe_resolve(document_root: Path, requested_name: str) -> Path:
    """Resolve a user-controlled file name under document_root.

    The HTTP boundary decodes URL escapes before calling this function. This
    function rejects absolute paths, resolves the final path, and requires it to
    remain under the resolved document root. It is intentionally small so the
    check can be audited in the blog.
    """

    root = document_root.resolve()
    candidate = Path(requested_name or "")
    if not requested_name or candidate.is_absolute():
        raise PathBoundaryError("empty or absolute paths are not allowed")
    resolved = (root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise PathBoundaryError("requested path leaves document root")
    if not resolved.is_file():
        raise PathBoundaryError("requested path is not a regular file")
    return resolved


def unsafe_join(document_root: Path, requested_name: str) -> Path:
    """Deliberately unsafe join for the local teaching endpoint."""

    return document_root / (requested_name or "")
