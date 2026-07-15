from __future__ import annotations

from fastapi.testclient import TestClient

from local_evidence.api import create_app


def test_fastapi_manifest_and_path_boundary(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "note.txt").write_text("hello", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    response = client.get("/manifest", params={"subpath": "data"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["root_name"] == "data"
    assert payload["summary"] == {"file_count": 1, "total_bytes": 5}

    escape = client.get("/manifest", params={"subpath": "../"})
    assert escape.status_code == 400
