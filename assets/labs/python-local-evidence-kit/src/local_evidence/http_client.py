from __future__ import annotations

from typing import Any

import httpx


class ServiceRequestError(RuntimeError):
    """Boundary error raised when a service request fails."""


def fetch_json(url: str, *, timeout: float = 2.0, client: httpx.Client | None = None) -> dict[str, Any]:
    """Fetch JSON with an explicit timeout and a single project-level error type."""
    try:
        if client is not None:
            response = client.get(url)
        else:
            with httpx.Client(timeout=timeout) as owned_client:
                response = owned_client.get(url)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ServiceRequestError(f"GET {url} failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ServiceRequestError(f"GET {url} did not return a JSON object")
    return payload


def summarize_manifest_payload(payload: dict[str, Any]) -> str:
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ServiceRequestError("manifest payload has no summary object")
    return f"files={summary.get('file_count')} bytes={summary.get('total_bytes')}"
