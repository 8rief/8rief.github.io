#!/usr/bin/env python3
"""Small HTTP service used to demonstrate startup, health checks and graceful shutdown."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


def now() -> float:
    return time.time()


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass
class LifecycleState:
    host: str
    port: int
    pid: int
    started_at: float
    startup_complete: bool = False
    shutdown_requested: bool = False
    stopping: bool = False
    active_requests: int = 0
    accepted_requests: int = 0
    completed_requests: int = 0
    refused_requests: int = 0
    events: list[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def mode(self) -> str:
        if self.stopping:
            return "stopping"
        if self.shutdown_requested:
            return "draining"
        if not self.startup_complete:
            return "starting"
        return "ready"

    def ready(self) -> bool:
        return self.startup_complete and not self.shutdown_requested and not self.stopping

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "pid": self.pid,
                "host": self.host,
                "port": self.port,
                "mode": self.mode(),
                "ready": self.ready(),
                "shutdown_requested": self.shutdown_requested,
                "active_requests": self.active_requests,
                "accepted_requests": self.accepted_requests,
                "completed_requests": self.completed_requests,
                "refused_requests": self.refused_requests,
                "uptime_ms": int((now() - self.started_at) * 1000),
            }

    def mark_ready(self) -> None:
        with self.lock:
            self.startup_complete = True

    def request_shutdown(self) -> bool:
        with self.lock:
            first = not self.shutdown_requested
            self.shutdown_requested = True
            return first

    def mark_stopping(self) -> None:
        with self.lock:
            self.stopping = True

    def try_accept_work(self) -> bool:
        with self.lock:
            if not self.startup_complete or self.shutdown_requested or self.stopping:
                self.refused_requests += 1
                return False
            self.active_requests += 1
            self.accepted_requests += 1
            return True

    def finish_work(self) -> None:
        with self.lock:
            self.active_requests -= 1
            self.completed_requests += 1

    def active_count(self) -> int:
        with self.lock:
            return self.active_requests


class JsonLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def emit(self, event: str, **fields: Any) -> None:
        payload = {"ts": round(now(), 6), "event": event, **fields}
        line = canonical_json(payload)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())


def make_handler(state: LifecycleState, logger: JsonLogger):
    class Handler(BaseHTTPRequestHandler):
        server_version = "LifecycleDemo/1.0"

        def log_message(self, fmt: str, *args: Any) -> None:  # keep stderr deterministic
            return

        def send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = canonical_json(payload).encode("utf-8") + b"\n"
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - http.server API name
            parsed = urlparse(self.path)
            if parsed.path == "/live":
                self.send_json(HTTPStatus.OK, {"ok": True, "check": "live", **state.snapshot()})
                return
            if parsed.path == "/ready":
                snap = state.snapshot()
                status = HTTPStatus.OK if snap["ready"] else HTTPStatus.SERVICE_UNAVAILABLE
                self.send_json(status, {"ok": snap["ready"], "check": "ready", **snap})
                return
            if parsed.path == "/status":
                self.send_json(HTTPStatus.OK, {"ok": True, **state.snapshot()})
                return
            if parsed.path == "/work":
                self.handle_work(parsed.query)
                return
            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})

        def handle_work(self, query: str) -> None:
            params = parse_qs(query)
            raw_seconds = params.get("seconds", ["0.05"])[0]
            try:
                seconds = float(raw_seconds)
            except ValueError:
                self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid_seconds"})
                return
            if seconds < 0 or seconds > 5:
                self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "seconds_out_of_range"})
                return
            if not state.try_accept_work():
                logger.emit("request_refused", path="/work", reason="not_ready_or_draining", **state.snapshot())
                self.send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"ok": False, "error": "not_ready_or_draining", **state.snapshot()})
                return
            logger.emit("request_started", path="/work", seconds=seconds, **state.snapshot())
            started = now()
            try:
                while now() - started < seconds:
                    time.sleep(min(0.05, seconds))
                state.finish_work()
                logger.emit("request_completed", path="/work", seconds=seconds, **state.snapshot())
                self.send_json(HTTPStatus.OK, {"ok": True, "worked_seconds": seconds, **state.snapshot()})
            except BrokenPipeError:
                state.finish_work()
                logger.emit("request_client_gone", path="/work", seconds=seconds, **state.snapshot())
                raise

    return Handler


def write_state_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run_service(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log_file) if args.log_file else state_dir / "events.jsonl"
    state_file = Path(args.state_file) if args.state_file else state_dir / "service_state.json"
    shutdown_event = threading.Event()

    logger = JsonLogger(log_path)
    httpd = ThreadingHTTPServer((args.host, args.port), lambda *a, **kw: None)
    host, port = httpd.server_address[:2]
    state = LifecycleState(host=host, port=int(port), pid=os.getpid(), started_at=now())
    httpd.RequestHandlerClass = make_handler(state, logger)

    def on_signal(signum: int, _frame: Any) -> None:
        if state.request_shutdown():
            logger.emit("shutdown_requested", signal=signum, **state.snapshot())
        shutdown_event.set()

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    write_state_file(
        state_file,
        {
            "pid": state.pid,
            "host": host,
            "port": int(port),
            "state_file": "service_state.json",
            "log_file": "events.jsonl",
        },
    )
    logger.emit("service_starting", pid=state.pid, host=host, port=int(port), startup_delay=args.startup_delay)

    serve_thread = threading.Thread(target=httpd.serve_forever, name="http-server", daemon=False)
    serve_thread.start()

    startup_deadline = now() + args.startup_delay
    while now() < startup_deadline:
        if shutdown_event.wait(timeout=min(0.05, startup_deadline - now())):
            break
    if not state.shutdown_requested:
        state.mark_ready()
        logger.emit("service_ready", **state.snapshot())

    while not shutdown_event.is_set():
        time.sleep(0.05)

    deadline = now() + args.grace_timeout
    timed_out = False
    while state.active_count() > 0 and now() < deadline:
        time.sleep(0.05)
    if state.active_count() > 0:
        timed_out = True
        logger.emit("drain_timeout", remaining_active_requests=state.active_count(), grace_timeout=args.grace_timeout, **state.snapshot())
    else:
        logger.emit("drain_complete", remaining_active_requests=0, **state.snapshot())

    state.mark_stopping()
    httpd.shutdown()
    httpd.server_close()
    serve_thread.join(timeout=2)
    logger.emit("service_stopped", timed_out=timed_out, **state.snapshot())
    return 2 if timed_out else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local lifecycle-demo HTTP service.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--state-file")
    parser.add_argument("--log-file")
    parser.add_argument("--startup-delay", type=float, default=0.2)
    parser.add_argument("--grace-timeout", type=float, default=3.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_service(args)


if __name__ == "__main__":
    raise SystemExit(main())
