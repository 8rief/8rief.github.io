#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "src" / "service_lifecycle_demo.py"


def read_json(url: str, timeout: float = 2.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def wait_for(fn, timeout=3.0, label="condition"):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = fn()
        if last:
            return last
        time.sleep(0.05)
    raise AssertionError(f"timeout waiting for {label}; last={last!r}")


class ServiceProcess:
    def __init__(self, startup_delay=0.1, grace_timeout=2.0):
        self.tmp = tempfile.TemporaryDirectory(prefix="svc-test-")
        self.state_dir = Path(self.tmp.name)
        self.proc = subprocess.Popen(
            [
                sys.executable,
                str(SERVICE),
                "--state-dir",
                str(self.state_dir),
                "--startup-delay",
                str(startup_delay),
                "--grace-timeout",
                str(grace_timeout),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        meta = wait_for(self._read_state, label="state file")
        self.base = f"http://{meta['host']}:{meta['port']}"

    def _read_state(self):
        p = self.state_dir / "service_state.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def stop(self):
        if self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=2)
        self.tmp.cleanup()

    def terminate(self, timeout=4):
        os.kill(self.proc.pid, signal.SIGTERM)
        return self.proc.wait(timeout=timeout)

    def events(self):
        path = self.state_dir / "events.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class LifecycleDemoTests(unittest.TestCase):
    def test_live_is_available_before_ready(self):
        svc = ServiceProcess(startup_delay=0.3)
        try:
            live_code, live = read_json(svc.base + "/live")
            ready_code, ready = read_json(svc.base + "/ready")
            self.assertEqual(live_code, 200)
            self.assertEqual(ready_code, 503)
            self.assertFalse(ready["ready"])
            wait_for(lambda: read_json(svc.base + "/ready")[0] == 200, label="ready")
            status_code, status = read_json(svc.base + "/status")
            self.assertEqual(status_code, 200)
            self.assertTrue(status["ready"])
            self.assertEqual(live["pid"], svc.proc.pid)
        finally:
            svc.stop()

    def test_work_updates_status_counters(self):
        svc = ServiceProcess(startup_delay=0.0)
        try:
            wait_for(lambda: read_json(svc.base + "/ready")[0] == 200, label="ready")
            code, payload = read_json(svc.base + "/work?seconds=0.05")
            self.assertEqual(code, 200)
            self.assertEqual(payload["accepted_requests"], 1)
            self.assertEqual(payload["completed_requests"], 1)
            self.assertEqual(payload["active_requests"], 0)
        finally:
            svc.stop()

    def test_sigterm_refuses_new_work_and_drains_active_request(self):
        svc = ServiceProcess(startup_delay=0.0, grace_timeout=3.0)
        try:
            wait_for(lambda: read_json(svc.base + "/ready")[0] == 200, label="ready")
            result = {}

            def call_work():
                result["code"], result["payload"] = read_json(svc.base + "/work?seconds=0.6", timeout=2.0)

            t = threading.Thread(target=call_work)
            t.start()
            wait_for(lambda: read_json(svc.base + "/status")[1]["active_requests"] == 1, label="active")
            os.kill(svc.proc.pid, signal.SIGTERM)
            wait_for(lambda: read_json(svc.base + "/ready")[0] == 503, label="not ready")
            refused_code, refused = read_json(svc.base + "/work?seconds=0")
            self.assertEqual(refused_code, 503)
            self.assertFalse(refused["ready"])
            t.join(timeout=3)
            self.assertFalse(t.is_alive())
            self.assertEqual(result["code"], 200)
            self.assertEqual(svc.proc.wait(timeout=4), 0)
            event_names = [e["event"] for e in svc.events()]
            self.assertIn("shutdown_requested", event_names)
            self.assertIn("request_refused", event_names)
            self.assertIn("drain_complete", event_names)
            self.assertIn("service_stopped", event_names)
        finally:
            svc.stop()

    def test_sigterm_without_active_work_exits_cleanly(self):
        svc = ServiceProcess(startup_delay=0.0, grace_timeout=1.0)
        try:
            wait_for(lambda: read_json(svc.base + "/ready")[0] == 200, label="ready")
            os.kill(svc.proc.pid, signal.SIGTERM)
            self.assertEqual(svc.proc.wait(timeout=3), 0)
            event_names = [e["event"] for e in svc.events()]
            self.assertIn("drain_complete", event_names)
            self.assertIn("service_stopped", event_names)
        finally:
            svc.stop()


if __name__ == "__main__":
    unittest.main()
