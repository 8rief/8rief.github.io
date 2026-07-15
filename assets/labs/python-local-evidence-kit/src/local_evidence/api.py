from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from .config import AppConfig
from .scanner import ScanBoundaryError, build_manifest


def _resolve_inside(base: Path, subpath: str) -> Path:
    candidate = (base / subpath).expanduser().resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="path escapes configured evidence root") from exc
    return candidate


def create_app(base_dir: Path | str | None = None) -> FastAPI:
    config = AppConfig.from_env()
    base = Path(base_dir).expanduser().resolve() if base_dir is not None else config.evidence_root
    app = FastAPI(title="Local Evidence Kit", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/manifest")
    def manifest(subpath: str = Query(".", description="Directory under the configured evidence root")) -> dict:
        target = _resolve_inside(base, subpath)
        try:
            return build_manifest(target).to_dict()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ScanBoundaryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
