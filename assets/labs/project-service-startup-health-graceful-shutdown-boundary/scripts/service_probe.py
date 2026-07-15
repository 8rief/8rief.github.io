#!/usr/bin/env python3
"""Run deterministic lifecycle scenarios and write public-safe reports."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "src" / "service_lifecycle_demo.py"
REPORTS = ROOT / "reports"


def read_json_url(url: str, timeout: float = 2.0) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(url, headers={"User-Agent": "service-lifecycle-probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def wait_for(predicate, timeout: float, label: str):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = predicate()
        if last:
            return last
        time.sleep(0.05)
    raise AssertionError(f"timeout waiting for {label}; last={last!r}")


def start_service(state_dir: Path, startup_delay: float = 0.2, grace_timeout: float = 3.0) -> subprocess.Popen[str]:
    cmd = [
        sys.executable,
        str(SERVICE),
        "--state-dir",
        str(state_dir),
        "--startup-delay",
        str(startup_delay),
        "--grace-timeout",
        str(grace_timeout),
    ]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)


def wait_state(state_dir: Path) -> dict[str, Any]:
    state_file = state_dir / "service_state.json"
    return wait_for(lambda: json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else None, 3, "state file")


def load_events(state_dir: Path) -> list[dict[str, Any]]:
    events = []
    path = state_dir / "events.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def terminate_and_collect(proc: subprocess.Popen[str], timeout: float = 5.0) -> int:
    try:
        return proc.wait(timeout=timeout)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=2)


def run_probe() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="service-lifecycle-") as tmp:
        state_dir = Path(tmp)
        proc = start_service(state_dir, startup_delay=0.35, grace_timeout=3.0)
        try:
            meta = wait_state(state_dir)
            base = f"http://{meta['host']}:{meta['port']}"
            live_code, live_before = read_json_url(base + "/live")
            ready_code_before, ready_before = read_json_url(base + "/ready")
            wait_for(lambda: read_json_url(base + "/ready")[0] == 200, 3, "ready=200")
            ready_code_after, ready_after = read_json_url(base + "/ready")

            result_holder: dict[str, Any] = {}

            def long_work() -> None:
                code, payload = read_json_url(base + "/work?seconds=0.8", timeout=3.0)
                result_holder["code"] = code
                result_holder["payload"] = payload

            worker = threading.Thread(target=long_work, daemon=True)
            worker.start()
            wait_for(lambda: read_json_url(base + "/status")[1].get("active_requests") == 1, 3, "active request")
            os.kill(proc.pid, signal.SIGTERM)
            wait_for(lambda: read_json_url(base + "/ready")[0] == 503, 3, "ready false after SIGTERM")
            refused_code, refused_payload = read_json_url(base + "/work?seconds=0.0")
            worker.join(timeout=4)
            if worker.is_alive():
                raise AssertionError("in-flight request did not finish")
            return_code = terminate_and_collect(proc, timeout=5)
            events = load_events(state_dir)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=2)

        event_names = [e.get("event") for e in events]
        required = {
            "service_starting",
            "service_ready",
            "request_started",
            "shutdown_requested",
            "request_refused",
            "request_completed",
            "drain_complete",
            "service_stopped",
        }
        summary = {
            "pid_file_valid": meta["pid"] == proc.pid and int(meta["port"]) > 0,
            "live_before_ready": live_code == 200 and ready_code_before == 503,
            "ready_after_startup": ready_code_after == 200 and ready_after.get("ready") is True,
            "sigterm_ready_false": refused_payload.get("ready") is False,
            "new_work_refused_during_drain": refused_code == 503,
            "inflight_completed": result_holder.get("code") == 200 and result_holder.get("payload", {}).get("completed_requests") == 1,
            "clean_exit": return_code == 0,
            "jsonl_events_valid": all(isinstance(e, dict) and "event" in e for e in events),
            "required_events_present": required.issubset(event_names),
            "event_count": len(events),
            "final_event_names": event_names,
            "live_before": live_before,
            "ready_before": ready_before,
            "ready_after": ready_after,
            "refused_payload": refused_payload,
            "work_payload": result_holder.get("payload"),
            "return_code": return_code,
        }
        summary["run_status"] = "ok" if all(
            summary[k]
            for k in [
                "pid_file_valid",
                "live_before_ready",
                "ready_after_startup",
                "new_work_refused_during_drain",
                "inflight_completed",
                "clean_exit",
                "jsonl_events_valid",
                "required_events_present",
            ]
        ) else "fail"
        return summary


def write_reports(summary: dict[str, Any]) -> None:
    (REPORTS / "service_lifecycle_probe.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Service lifecycle probe transcript",
        "",
        f"PID_PORT_FILE_VALID={'yes' if summary['pid_file_valid'] else 'no'}",
        f"LIVE_BEFORE_READY={'yes' if summary['live_before_ready'] else 'no'}",
        f"READY_AFTER_STARTUP={'yes' if summary['ready_after_startup'] else 'no'}",
        f"SIGTERM_READY_FALSE={'yes' if summary['sigterm_ready_false'] else 'no'}",
        f"NEW_WORK_REFUSED_DURING_DRAIN={'yes' if summary['new_work_refused_during_drain'] else 'no'}",
        f"INFLIGHT_COMPLETED_BEFORE_EXIT={'yes' if summary['inflight_completed'] else 'no'}",
        f"SERVICE_EXIT_CODE={summary['return_code']}",
        f"REQUIRED_EVENTS_PRESENT={'yes' if summary['required_events_present'] else 'no'}",
        f"JSONL_EVENTS_VALID={'yes' if summary['jsonl_events_valid'] else 'no'}",
        f"EVENT_COUNT={summary['event_count']}",
        f"RUN_STATUS={summary['run_status']}",
        "",
        "## Events",
        "",
        "```text",
        ", ".join(summary["final_event_names"]),
        "```",
    ]
    (REPORTS / "transcript.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    status_lines = [
        "# Service lifecycle status report",
        "",
        "| Check | Result | Meaning |",
        "| --- | --- | --- |",
        f"| PID/port file | {'PASS' if summary['pid_file_valid'] else 'FAIL'} | service wrote a discoverable local endpoint |",
        f"| live before ready | {'PASS' if summary['live_before_ready'] else 'FAIL'} | liveness and readiness are separate |",
        f"| ready after startup | {'PASS' if summary['ready_after_startup'] else 'FAIL'} | initialization gate works |",
        f"| SIGTERM readiness | {'PASS' if summary['sigterm_ready_false'] else 'FAIL'} | shutdown removes service from traffic |",
        f"| drain refusal | {'PASS' if summary['new_work_refused_during_drain'] else 'FAIL'} | no new work is accepted after shutdown starts |",
        f"| in-flight completion | {'PASS' if summary['inflight_completed'] else 'FAIL'} | already-started work can finish before exit |",
        f"| lifecycle events | {'PASS' if summary['required_events_present'] else 'FAIL'} | logs preserve startup/work/shutdown evidence |",
    ]
    (REPORTS / "service_status_report.md").write_text("\n".join(status_lines) + "\n", encoding="utf-8")


def main() -> int:
    summary = run_probe()
    write_reports(summary)
    print((REPORTS / "transcript.md").read_text(encoding="utf-8"))
    return 0 if summary["run_status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
