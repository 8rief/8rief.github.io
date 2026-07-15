from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .path_safety import PathBoundaryError, safe_resolve, unsafe_join


class LocalLabServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler, public_dir: Path, outside_dir: Path):
        super().__init__(server_address, handler)
        self.public_dir = public_dir.resolve()
        self.outside_dir = outside_dir.resolve()
        self.ready_event = threading.Event()


class LocalLabHandler(BaseHTTPRequestHandler):
    server: LocalLabServer

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        super().end_headers()

    def do_HEAD(self) -> None:
        self._route(send_body=False)

    def do_GET(self) -> None:
        self._route(send_body=True)

    def do_POST(self) -> None:
        self._json(
            HTTPStatus.METHOD_NOT_ALLOWED,
            {"error": "method not allowed"},
            extra_headers={"Allow": "GET, HEAD"},
        )

    def _route(self, send_body: bool) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/health":
            self._json(HTTPStatus.OK, {"status": "ok", "bind": self.server.server_address[0]}, send_body=send_body)
        elif parsed.path == "/headers":
            self._json(
                HTTPStatus.OK,
                {"method": self.command, "path": parsed.path, "headers": dict(self.headers)},
                send_body=send_body,
            )
        elif parsed.path == "/safe-file":
            self._serve_safe(query.get("name", [""])[0], send_body=send_body)
        elif parsed.path == "/unsafe-file":
            self._serve_unsafe(query.get("name", [""])[0], send_body=send_body)
        else:
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"}, send_body=send_body)

    def _serve_safe(self, name: str, send_body: bool) -> None:
        try:
            path = safe_resolve(self.server.public_dir, name)
        except PathBoundaryError as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)}, send_body=send_body)
            return
        self._text(HTTPStatus.OK, path.read_text(encoding="utf-8"), send_body=send_body)

    def _serve_unsafe(self, name: str, send_body: bool) -> None:
        path = unsafe_join(self.server.public_dir, name)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)}, send_body=send_body)
            return
        self._text(HTTPStatus.OK, text, send_body=send_body)

    def _json(
        self,
        status: HTTPStatus,
        data: object,
        send_body: bool = True,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def _text(self, status: HTTPStatus, text: str, send_body: bool = True) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)


def make_server(host: str, port: int, public_dir: Path, outside_dir: Path) -> LocalLabServer:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("server host must be loopback for this lab")
    server = LocalLabServer((host, port), LocalLabHandler, public_dir=public_dir, outside_dir=outside_dir)
    server.ready_event.set()
    return server


def serve_forever(host: str, port: int, public_dir: Path, outside_dir: Path) -> None:
    server = make_server(host, port, public_dir, outside_dir)
    print(f"ready http://{host}:{server.server_port}/health", flush=True)
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()
