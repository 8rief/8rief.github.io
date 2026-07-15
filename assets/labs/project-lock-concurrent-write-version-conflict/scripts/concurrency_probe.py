#!/usr/bin/env python3
"""Run deterministic subprocess experiments for local concurrent writers."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
REPORTS = ROOT / "reports"
sys.path.insert(0, str(SRC))

from versioned_counter import atomic_write_state, initial_state, read_state  # noqa: E402


def command(*parts: object) -> list[str]:
    return [sys.executable, str(SRC / "versioned_counter.py"), *(str(part) for part in parts)]


def portable_argv(argv: list[str]) -> list[str]:
    portable: list[str] = []
    for part in argv:
        if part == sys.executable:
            portable.append("python3")
        elif part == str(SRC / "versioned_counter.py"):
            portable.append("src/versioned_counter.py")
        elif part.startswith(str(ROOT)):
            portable.append("$LAB" + part[len(str(ROOT)) :])
        elif part.startswith(tempfile.gettempdir()):
            portable.append("$RUN/" + Path(part).name)
        else:
            portable.append(part)
    return portable


def run_workers(commands: list[list[str]]) -> list[subprocess.CompletedProcess[str]]:
    processes = [
        subprocess.Popen(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for argv in commands
    ]
    results: list[subprocess.CompletedProcess[str]] = []
    for process, argv in zip(processes, commands, strict=True):
        stdout, stderr = process.communicate(timeout=10)
        results.append(subprocess.CompletedProcess(argv, process.returncode, stdout, stderr))
    return results


def result_record(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return {
        "argv": portable_argv(result.args),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def wait_for(path: Path, timeout_seconds: float = 3.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError(f"timed out waiting for {path.name}")
        time.sleep(0.01)


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="counter-concurrency-") as directory:
        run = Path(directory)
        state = run / "counter.json"
        lock = run / "counter.lock"

        atomic_write_state(state, initial_state())
        unsafe_commands = [
            command("unsafe", "--state", state, "--ready-dir", run / "unsafe-ready", "--worker-id", "A", "--delay-ms", 120),
            command("unsafe", "--state", state, "--ready-dir", run / "unsafe-ready", "--worker-id", "B", "--delay-ms", 0),
        ]
        unsafe_results = run_workers(unsafe_commands)
        unsafe_state = read_state(state)

        atomic_write_state(state, initial_state())
        locked_commands = [
            command("locked", "--state", state, "--lock", lock, "--hold-ms", 100, "--timeout-ms", 2000),
            command("locked", "--state", state, "--lock", lock, "--hold-ms", 0, "--timeout-ms", 2000),
        ]
        locked_results = run_workers(locked_commands)
        locked_state = read_state(state)

        atomic_write_state(state, initial_state())
        cas_commands = [
            command("cas", "--state", state, "--lock", lock, "--expected-version", 0, "--ready-dir", run / "cas-ready", "--worker-id", "A", "--delay-ms", 120, "--timeout-ms", 2000),
            command("cas", "--state", state, "--lock", lock, "--expected-version", 0, "--ready-dir", run / "cas-ready", "--worker-id", "B", "--delay-ms", 0, "--timeout-ms", 2000),
        ]
        cas_results = run_workers(cas_commands)
        cas_after_conflict = read_state(state)
        retry = subprocess.run(
            command("cas", "--state", state, "--lock", lock, "--expected-version", 1, "--timeout-ms", 2000),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        cas_after_retry = read_state(state)

        holder_ready = run / "holder.ready"
        holder = subprocess.Popen(
            command("hold-lock", "--lock", lock, "--ready", holder_ready, "--hold-ms", 400),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        wait_for(holder_ready)
        timeout_result = subprocess.run(
            command("locked", "--state", state, "--lock", lock, "--timeout-ms", 60),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        holder_stdout, holder_stderr = holder.communicate(timeout=10)
        holder_result = subprocess.CompletedProcess(
            command("hold-lock", "--lock", lock, "--ready", holder_ready, "--hold-ms", 400),
            holder.returncode,
            holder_stdout,
            holder_stderr,
        )

        conflict_count = sum(result.returncode == 73 for result in cas_results)
        success_count = sum(result.returncode == 0 for result in cas_results)
        report = {
            "schema_version": 1,
            "unsafe": {
                "workers": [result_record(result) for result in unsafe_results],
                "final_state": unsafe_state,
                "lost_update": unsafe_state["value"] == 1,
            },
            "locked": {
                "workers": [result_record(result) for result in locked_results],
                "final_state": locked_state,
                "serialized": locked_state["value"] == 2,
                "stable_separate_lock_file": lock.name == "counter.lock" and state.name == "counter.json",
            },
            "optimistic": {
                "workers": [result_record(result) for result in cas_results],
                "after_conflict": cas_after_conflict,
                "success_count": success_count,
                "conflict_count": conflict_count,
                "conflict_return_code": 73,
                "retry": result_record(retry),
                "after_retry": cas_after_retry,
            },
            "timeout": {
                "holder": result_record(holder_result),
                "contender": result_record(timeout_result),
                "timeout_return_code": 75,
            },
        }

        checks = {
            "unsafe_workers_succeeded": all(result.returncode == 0 for result in unsafe_results),
            "unsafe_lost_update": unsafe_state == {"schema_version": 1, "version": 1, "value": 1},
            "locked_workers_succeeded": all(result.returncode == 0 for result in locked_results),
            "locked_serialized": locked_state == {"schema_version": 1, "version": 2, "value": 2},
            "cas_one_success_one_conflict": success_count == 1 and conflict_count == 1,
            "cas_retry_succeeded": retry.returncode == 0 and cas_after_retry == {"schema_version": 1, "version": 2, "value": 2},
            "lock_timeout_bounded": holder_result.returncode == 0 and timeout_result.returncode == 75,
            "state_json_valid": all(
                item["schema_version"] == 1 and item["version"] == item["value"]
                for item in (unsafe_state, locked_state, cas_after_conflict, cas_after_retry)
            ),
        }
        if not all(checks.values()):
            raise AssertionError(json.dumps(checks, indent=2, sort_keys=True))
        report["checks"] = checks
        (REPORTS / "concurrency_probe.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        lines = [
            "# Concurrent writer transcript",
            "",
            "The probe launches real Python subprocesses on one local Linux filesystem.",
            "",
            "```text",
            f"UNSAFE_FINAL_VALUE={unsafe_state['value']}",
            f"UNSAFE_LOST_UPDATE={'yes' if checks['unsafe_lost_update'] else 'no'}",
            f"LOCKED_FINAL_VALUE={locked_state['value']}",
            f"LOCKED_SERIALIZED={'yes' if checks['locked_serialized'] else 'no'}",
            f"CAS_SUCCESS_COUNT={success_count}",
            f"CAS_CONFLICT_COUNT={conflict_count}",
            "CAS_CONFLICT_RC=73",
            f"CAS_RETRY_FINAL_VALUE={cas_after_retry['value']}",
            "LOCK_TIMEOUT_RC=75",
            f"STATE_JSON_VALID={'yes' if checks['state_json_valid'] else 'no'}",
            "RUN_STATUS=ok",
            "```",
            "",
        ]
        (REPORTS / "transcript.md").write_text("\n".join(lines), encoding="utf-8")
        (REPORTS / "version_conflict_summary.md").write_text(
            "# Version conflict summary\n\n"
            "Atomic replacement kept every observed file complete, but did not protect the read-modify-write sequence. "
            "A stable advisory lock serialized pessimistic writers. The optimistic path used the same short lock only "
            "for the version check plus replacement: one stale writer returned 73, then reread and retried successfully. "
            "A contending writer returned 75 after a bounded wait.\n",
            encoding="utf-8",
        )

        print(f"UNSAFE_FINAL_VALUE={unsafe_state['value']}")
        print("UNSAFE_LOST_UPDATE=yes")
        print(f"LOCKED_FINAL_VALUE={locked_state['value']}")
        print("LOCKED_SERIALIZED=yes")
        print(f"CAS_SUCCESS_COUNT={success_count}")
        print(f"CAS_CONFLICT_COUNT={conflict_count}")
        print("CAS_CONFLICT_RC=73")
        print(f"CAS_RETRY_FINAL_VALUE={cas_after_retry['value']}")
        print("LOCK_TIMEOUT_RC=75")
        print("STATE_JSON_VALID=yes")
        print("RUN_STATUS=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
