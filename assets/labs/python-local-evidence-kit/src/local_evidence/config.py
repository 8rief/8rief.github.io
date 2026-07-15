from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    evidence_root: Path
    log_level: str = "INFO"
    timeout_seconds: float = 2.0

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            evidence_root=Path(os.getenv("LOCAL_EVIDENCE_ROOT", ".")).expanduser().resolve(),
            log_level=os.getenv("LOCAL_EVIDENCE_LOG_LEVEL", "INFO").upper(),
            timeout_seconds=float(os.getenv("LOCAL_EVIDENCE_TIMEOUT", "2.0")),
        )
