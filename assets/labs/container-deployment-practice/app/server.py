#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

APP_VERSION = "1.0.0"
DEFAULT_PORT = 8080


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "/data"))


def app_name() -> str:
    return os.environ.get("APP_NAME", "container-lab")


def state_path(root: Path | None = None) -> Path:
    return (root or data_dir()) / "state.json"


def load_state(root: Path | None = None) -> dict[str, Any]:
    path = state_path(root)
    if not path.exists():
        return {"visits": 0, "events": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.setdefault("visits", 0)
    payload.setdefault("events", [])
    return payload


def save_state(state: dict[str, Any], root: Path | None = None) -> None:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def record_visit(label: str, root: Path | None = None) -> dict[str, Any]:
    clean_label = label.strip()[:40] or "anonymous"
    state = load_state(root)
    state["visits"] = int(state.get("visits", 0)) + 1
    state.setdefault("events", []).append({"label": clean_label, "at": utc_now()})
    state["events"] = state["events"][-20:]
    save_state(state, root)
    return state


def public_config() -> dict[str, Any]:
    return {
        "app_name": app_name(),
        "version": APP_VERSION,
        "data_dir": str(data_dir()),
        "container_note": "configuration is provided through environment variables; secrets are not printed",
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "ContainerLabHTTP/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}", flush=True)

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json({"status": "ok", "app": app_name(), "version": APP_VERSION})
            return
        if parsed.path == "/config":
            self.send_json(public_config())
            return
        if parsed.path == "/visits":
            params = parse_qs(parsed.query)
            label = params.get("label", ["browser"])[0]
            state = record_visit(label)
            self.send_json({"status": "recorded", "visits": state["visits"], "last_label": label[:40] or "anonymous"})
            return
        if parsed.path == "/state":
            state = load_state()
            self.send_json({"status": "ok", "visits": state["visits"], "event_count": len(state["events"])})
            return
        self.send_json({"status": "not_found", "path": parsed.path}, HTTPStatus.NOT_FOUND)


def main() -> None:
    port = int(os.environ.get("PORT", str(DEFAULT_PORT)))
    data_dir().mkdir(parents=True, exist_ok=True)
    addr = ("0.0.0.0", port)
    print(f"starting app={app_name()} version={APP_VERSION} port={port} data_dir={data_dir()}", flush=True)
    ThreadingHTTPServer(addr, Handler).serve_forever()


if __name__ == "__main__":
    main()
