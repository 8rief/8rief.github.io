#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from http_api_demo import make_server

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def http_request(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request_headers = {"X-Request-Id": f"probe-{method.lower()}-{path.strip('/').replace('/', '-') or 'root'}"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(base_url + path, data=data, method=method, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            raw = response.read()
            body = json.loads(raw.decode("utf-8")) if raw else None
            return {"method": method, "path": path, "status": response.status, "headers": dict(response.headers), "body": body}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        body = json.loads(raw.decode("utf-8")) if raw else None
        return {"method": method, "path": path, "status": exc.code, "headers": dict(exc.headers), "body": body}


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    server = make_server()
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{host}:{port}"
    events: list[dict[str, Any]] = []
    try:
        events.append(http_request(base_url, "GET", "/health"))
        events.append(http_request(base_url, "GET", "/tasks"))
        events.append(http_request(base_url, "POST", "/tasks", {"title": ""}))
        events.append(http_request(base_url, "POST", "/tasks", {"title": "write API contract"}, {"Idempotency-Key": "contract-demo"}))
        events.append(http_request(base_url, "POST", "/tasks", {"title": "write API contract"}, {"Idempotency-Key": "contract-demo"}))
        events.append(http_request(base_url, "POST", "/tasks", {"title": "changed title"}, {"Idempotency-Key": "contract-demo"}))
        events.append(http_request(base_url, "GET", "/tasks/tsk-001"))
        events.append(http_request(base_url, "PUT", "/tasks/tsk-001", {"title": "write API contract", "done": True}))
        events.append(http_request(base_url, "PUT", "/tasks/tsk-001", {"title": "write API contract", "done": True}))
        events.append(http_request(base_url, "GET", "/tasks/tsk-999"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    create = events[3]
    replay = events[4]
    conflict = events[5]
    put_first = events[7]
    put_repeat = events[8]
    not_found = events[9]
    summary = {
        "base_url_shape": "http://127.0.0.1:<ephemeral>",
        "event_count": len(events),
        "health_status": events[0]["status"],
        "list_status": events[1]["status"],
        "validation_status": events[2]["status"],
        "validation_error_code": events[2]["body"]["error"]["code"],
        "create_status": create["status"],
        "created_location": create["headers"].get("Location"),
        "created_task_id": create["body"]["task"]["id"],
        "replay_status": replay["status"],
        "replay_same_id": replay["body"]["task"]["id"] == create["body"]["task"]["id"],
        "replay_header": replay["headers"].get("Idempotency-Replayed") == "true",
        "conflict_status": conflict["status"],
        "conflict_error_code": conflict["body"]["error"]["code"],
        "get_status": events[6]["status"],
        "put_status": put_first["status"],
        "put_changed": put_first["body"]["changed"],
        "put_repeat_changed": put_repeat["body"]["changed"],
        "not_found_status": not_found["status"],
        "not_found_error_code": not_found["body"]["error"]["code"],
        "all_responses_have_request_id": all("X-Request-Id" in event["headers"] for event in events),
    }

    (REPORTS / "api_events.jsonl").write_text("".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in events), encoding="utf-8")
    (REPORTS / "api_contract_probe.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (REPORTS / "api_contract_report.md").write_text(render_report(summary), encoding="utf-8")

    print("HEALTH_STATUS=%s" % summary["health_status"])
    print("LIST_STATUS=%s" % summary["list_status"])
    print("VALIDATION_STATUS=%s" % summary["validation_status"])
    print("VALIDATION_ERROR_CODE=%s" % summary["validation_error_code"])
    print("CREATE_STATUS=%s" % summary["create_status"])
    print("CREATED_LOCATION=%s" % summary["created_location"])
    print("CREATED_TASK_ID=%s" % summary["created_task_id"])
    print("REPLAY_STATUS=%s" % summary["replay_status"])
    print("REPLAY_SAME_ID=%s" % yes(summary["replay_same_id"]))
    print("REPLAY_HEADER=%s" % yes(summary["replay_header"]))
    print("CONFLICT_STATUS=%s" % summary["conflict_status"])
    print("CONFLICT_ERROR_CODE=%s" % summary["conflict_error_code"])
    print("GET_STATUS=%s" % summary["get_status"])
    print("PUT_STATUS=%s" % summary["put_status"])
    print("PUT_CHANGED=%s" % yes(summary["put_changed"]))
    print("PUT_REPEAT_CHANGED=%s" % yes(summary["put_repeat_changed"]))
    print("NOT_FOUND_STATUS=%s" % summary["not_found_status"])
    print("NOT_FOUND_ERROR_CODE=%s" % summary["not_found_error_code"])
    print("REQUEST_IDS_PRESENT=%s" % yes(summary["all_responses_have_request_id"]))
    print("RUN_STATUS=ok")
    return 0


def yes(value: bool) -> str:
    return "yes" if value else "no"


def render_report(summary: dict[str, Any]) -> str:
    return f"""# HTTP API contract probe report

This report is generated by `scripts/api_contract_probe.py`.

| Check | Result |
| --- | --- |
| health status | {summary['health_status']} |
| invalid POST status | {summary['validation_status']} / {summary['validation_error_code']} |
| create status | {summary['create_status']} |
| created Location | {summary['created_location']} |
| replay same task id | {yes(summary['replay_same_id'])} |
| idempotency conflict | {summary['conflict_status']} / {summary['conflict_error_code']} |
| first PUT changed | {yes(summary['put_changed'])} |
| repeated PUT changed | {yes(summary['put_repeat_changed'])} |
| not found | {summary['not_found_status']} / {summary['not_found_error_code']} |
| response request IDs | {yes(summary['all_responses_have_request_id'])} |

The probe proves the public API contract at the HTTP boundary: method, path, status code, JSON body, error shape, selected headers, and retry/idempotency behavior.
"""


if __name__ == "__main__":
    raise SystemExit(main())
