from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request

from http_api_demo import TaskStore, make_server


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def request(self, method: str, path: str, payload: dict | None = None, headers: dict | None = None):
        data = None
        request_headers = {"X-Request-Id": "test-req"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        if headers:
            request_headers.update(headers)
        req = urllib.request.Request(self.base_url + path, data=data, method=method, headers=request_headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                raw = response.read()
                body = json.loads(raw.decode("utf-8")) if raw else None
                return response.status, dict(response.headers), body
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            body = json.loads(raw.decode("utf-8")) if raw else None
            return exc.code, dict(exc.headers), body


class HttpApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = make_server()
        host, port = self.server.server_address
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = ApiClient(f"http://{host}:{port}")

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def test_create_returns_201_location_and_replayable_idempotency_key(self):
        status, headers, body = self.client.request(
            "POST", "/tasks", {"title": "write API contract"}, {"Idempotency-Key": "lesson-1"}
        )
        self.assertEqual(status, 201)
        self.assertEqual(headers["Location"], "/tasks/tsk-001")
        self.assertEqual(body["task"]["id"], "tsk-001")

        replay_status, replay_headers, replay_body = self.client.request(
            "POST", "/tasks", {"title": "write API contract"}, {"Idempotency-Key": "lesson-1"}
        )
        self.assertEqual(replay_status, 201)
        self.assertEqual(replay_body["task"]["id"], "tsk-001")
        self.assertEqual(replay_headers["Idempotency-Replayed"], "true")

    def test_idempotency_key_rejects_different_payload(self):
        self.client.request("POST", "/tasks", {"title": "first"}, {"Idempotency-Key": "same-key"})
        status, _headers, body = self.client.request(
            "POST", "/tasks", {"title": "different"}, {"Idempotency-Key": "same-key"}
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["error"]["code"], "idempotency_conflict")

    def test_put_is_idempotent_when_state_does_not_change(self):
        self.client.request("POST", "/tasks", {"title": "ship"})
        first_status, _headers, first = self.client.request("PUT", "/tasks/tsk-001", {"title": "ship", "done": True})
        second_status, _headers, second = self.client.request("PUT", "/tasks/tsk-001", {"title": "ship", "done": True})
        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 200)
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertEqual(first["task"]["version"], second["task"]["version"])

    def test_errors_have_stable_shape_and_request_id(self):
        status, headers, body = self.client.request("POST", "/tasks", {"title": ""})
        self.assertEqual(status, 400)
        self.assertEqual(headers["X-Request-Id"], "test-req")
        self.assertEqual(body["error"]["code"], "validation_error")
        self.assertEqual(body["error"]["request_id"], "test-req")


class StoreUnitTests(unittest.TestCase):
    def test_fingerprint_is_order_independent(self):
        self.assertEqual(
            TaskStore.fingerprint({"title": "a", "done": False}),
            TaskStore.fingerprint({"done": False, "title": "a"}),
        )


if __name__ == "__main__":
    unittest.main()
