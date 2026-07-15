from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    name: str

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("project name must not be empty")
        if self.root == Path("/"):
            raise ValueError("refuse to use filesystem root as a project root")


def project_paths(root: Path) -> dict[str, Path]:
    return {
        "src": root / "src",
        "tests": root / "tests",
        "docs": root / "docs",
        "scripts": root / "scripts",
        "reports": root / "reports",
        "config": root / "config",
        "data": root / "data",
    }
