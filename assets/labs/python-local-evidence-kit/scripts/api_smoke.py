from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from local_evidence.api import create_app

root = Path(__file__).resolve().parents[1]
client = TestClient(create_app(root))
print("api /health ->", client.get("/health").json())
manifest = client.get("/manifest", params={"subpath": "sample_data"})
manifest.raise_for_status()
payload = manifest.json()
print("api /manifest sample_data ->", payload["summary"])
