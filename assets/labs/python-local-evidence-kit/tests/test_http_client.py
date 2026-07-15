from __future__ import annotations

import httpx
import pytest

from local_evidence.http_client import ServiceRequestError, fetch_json, summarize_manifest_payload


def test_http_client_fetches_and_summarizes_json():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/manifest"
        return httpx.Response(200, json={"summary": {"file_count": 3, "total_bytes": 42}})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://local") as client:
        payload = fetch_json("http://local/manifest", client=client)

    assert summarize_manifest_payload(payload) == "files=3 bytes=42"


def test_http_client_raises_project_error_on_status():
    transport = httpx.MockTransport(lambda request: httpx.Response(500, json={"error": "boom"}))
    with httpx.Client(transport=transport, base_url="http://local") as client:
        with pytest.raises(ServiceRequestError):
            fetch_json("http://local/manifest", client=client)
