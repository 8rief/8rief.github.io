from __future__ import annotations

import httpx

from local_evidence.http_client import fetch_json, summarize_manifest_payload


def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"summary": {"file_count": 3, "total_bytes": 42}})


with httpx.Client(transport=httpx.MockTransport(handler), base_url="http://local") as client:
    payload = fetch_json("http://local/manifest", client=client)
print("http client mock ->", summarize_manifest_payload(payload))
