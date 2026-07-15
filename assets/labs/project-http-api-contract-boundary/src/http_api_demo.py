#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import uuid
from dataclasses import dataclass, asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    done: bool
    version: int


@dataclass(frozen=True)
class StoredResponse:
    status: int
    headers: dict[str, str]
    body: dict[str, Any]
    fingerprint: str


class TaskStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._next_id = 1
        self._tasks: dict[str, Task] = {}
        self._idempotency: dict[str, StoredResponse] = {}

    @staticmethod
    def fingerprint(payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def list_tasks(self) -> list[dict[str, Any]]:
        with self._lock:
            return [asdict(task) for task in sorted(self._tasks.values(), key=lambda t: t.id)]

    def get_task(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks.get(task_id)

    def create_task(self, payload: dict[str, Any], idempotency_key: str | None) -> tuple[int, dict[str, str], dict[str, Any]]:
        title = validate_title(payload)
        done = bool(payload.get("done", False))
        fp = self.fingerprint({"title": title, "done": done})
        with self._lock:
            if idempotency_key and idempotency_key in self._idempotency:
                stored = self._idempotency[idempotency_key]
                if stored.fingerprint != fp:
                    body = error_body("idempotency_conflict", "same Idempotency-Key was used with a different request body", "")
                    return HTTPStatus.CONFLICT, {}, body
                headers = dict(stored.headers)
                headers["Idempotency-Replayed"] = "true"
                return stored.status, headers, dict(stored.body)

            task_id = f"tsk-{self._next_id:03d}"
            self._next_id += 1
            task = Task(id=task_id, title=title, done=done, version=1)
            self._tasks[task_id] = task
            body = {"task": asdict(task)}
            headers = {"Location": f"/tasks/{task_id}"}
            if idempotency_key:
                self._idempotency[idempotency_key] = StoredResponse(
                    status=HTTPStatus.CREATED,
                    headers=headers,
                    body=body,
                    fingerprint=fp,
                )
            return HTTPStatus.CREATED, headers, body

    def replace_task(self, task_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, str], dict[str, Any]]:
        title = validate_title(payload)
        if "done" not in payload or not isinstance(payload["done"], bool):
            raise ValidationError("field 'done' must be a boolean")
        with self._lock:
            old = self._tasks.get(task_id)
            if old is None:
                return HTTPStatus.NOT_FOUND, {}, error_body("not_found", f"task {task_id} does not exist", "")
            changed = old.title != title or old.done != payload["done"]
            version = old.version + 1 if changed else old.version
            new = Task(id=task_id, title=title, done=payload["done"], version=version)
            self._tasks[task_id] = new
            return HTTPStatus.OK, {}, {"task": asdict(new), "changed": changed}


class ValidationError(ValueError):
    pass


def validate_title(payload: dict[str, Any]) -> str:
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("field 'title' must be a non-empty string")
    return title.strip()


def error_body(code: str, message: str, request_id: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


def make_handler(store: TaskStore) -> type[BaseHTTPRequestHandler]:
    class TaskApiHandler(BaseHTTPRequestHandler):
        server_version = "TaskApiDemo/1.0"
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:  # keep tests/probe output deterministic
            return

        def do_GET(self) -> None:
            request_id = self.request_id()
            path = urlparse(self.path).path
            if path == "/health":
                self.send_json(HTTPStatus.OK, {"status": "ok", "request_id": request_id}, request_id=request_id)
                return
            if path == "/tasks":
                self.send_json(HTTPStatus.OK, {"tasks": store.list_tasks(), "request_id": request_id}, request_id=request_id)
                return
            task_id = match_task_path(path)
            if task_id:
                task = store.get_task(task_id)
                if task is None:
                    self.send_json(HTTPStatus.NOT_FOUND, error_body("not_found", f"task {task_id} does not exist", request_id), request_id=request_id)
                    return
                self.send_json(HTTPStatus.OK, {"task": asdict(task), "request_id": request_id}, request_id=request_id)
                return
            self.send_json(HTTPStatus.NOT_FOUND, error_body("not_found", f"path {path} is not defined", request_id), request_id=request_id)

        def do_POST(self) -> None:
            request_id = self.request_id()
            path = urlparse(self.path).path
            if path != "/tasks":
                self.send_json(HTTPStatus.NOT_FOUND, error_body("not_found", f"path {path} is not defined", request_id), request_id=request_id)
                return
            try:
                payload = self.read_json()
                status, headers, body = store.create_task(payload, self.headers.get("Idempotency-Key"))
            except ValidationError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, error_body("validation_error", str(exc), request_id), request_id=request_id)
                return
            except JsonRequestError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, error_body("bad_json", str(exc), request_id), request_id=request_id)
                return
            body.setdefault("request_id", request_id)
            self.send_json(status, body, extra_headers=headers, request_id=request_id)

        def do_PUT(self) -> None:
            request_id = self.request_id()
            task_id = match_task_path(urlparse(self.path).path)
            if not task_id:
                self.send_json(HTTPStatus.NOT_FOUND, error_body("not_found", f"path {self.path} is not defined", request_id), request_id=request_id)
                return
            try:
                payload = self.read_json()
                status, headers, body = store.replace_task(task_id, payload)
            except ValidationError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, error_body("validation_error", str(exc), request_id), request_id=request_id)
                return
            except JsonRequestError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, error_body("bad_json", str(exc), request_id), request_id=request_id)
                return
            patch_request_id(body, request_id)
            self.send_json(status, body, extra_headers=headers, request_id=request_id)

        def read_json(self) -> dict[str, Any]:
            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                raise JsonRequestError("Content-Type must be application/json")
            raw_len = self.headers.get("Content-Length")
            try:
                size = int(raw_len or "0")
            except ValueError as exc:
                raise JsonRequestError("Content-Length must be an integer") from exc
            if size <= 0:
                raise JsonRequestError("request body is empty")
            if size > 8192:
                raise JsonRequestError("request body is too large for this demo")
            raw = self.rfile.read(size)
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise JsonRequestError("request body must be valid UTF-8 JSON") from exc
            if not isinstance(data, dict):
                raise JsonRequestError("top-level JSON value must be an object")
            return data

        def request_id(self) -> str:
            incoming = self.headers.get("X-Request-Id")
            if incoming and all(ch.isalnum() or ch in "-_" for ch in incoming) and len(incoming) <= 80:
                return incoming
            return f"req-{uuid.uuid4().hex[:12]}"

        def send_json(
            self,
            status: int,
            body: dict[str, Any],
            *,
            extra_headers: dict[str, str] | None = None,
            request_id: str,
        ) -> None:
            encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("X-Request-Id", request_id)
            if extra_headers:
                for key, value in extra_headers.items():
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(encoded)

    return TaskApiHandler


class JsonRequestError(ValueError):
    pass


def match_task_path(path: str) -> str | None:
    parts = [p for p in path.split("/") if p]
    if len(parts) == 2 and parts[0] == "tasks" and parts[1].startswith("tsk-"):
        return parts[1]
    return None


def patch_request_id(body: dict[str, Any], request_id: str) -> None:
    if "error" in body and isinstance(body["error"], dict):
        body["error"]["request_id"] = request_id
    else:
        body.setdefault("request_id", request_id)


def make_server(host: str = "127.0.0.1", port: int = 0, store: TaskStore | None = None) -> ThreadingHTTPServer:
    api_store = store if store is not None else TaskStore()
    return ThreadingHTTPServer((host, port), make_handler(api_store))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the teaching HTTP task API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)
    if args.host not in {"127.0.0.1", "localhost"}:
        print("This teaching server binds only to local loopback hosts.", file=sys.stderr)
        return 64
    server = make_server(args.host, args.port)
    host, port = server.server_address
    print(f"TASK_API_LISTENING http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("TASK_API_STOPPING", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
