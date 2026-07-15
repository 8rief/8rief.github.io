#!/usr/bin/env python3
"""Run success and failure cases for the config/logging teaching package."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
WORK = Path("/tmp/project-config-log-lab")
APP = ROOT / "src" / "demo_app.py"
DEFAULTS = ROOT / "config" / "defaults.json"
DEVELOPMENT = ROOT / "config" / "development.json"
SECRET_VALUE = "probe-token-value-must-never-appear"


@dataclass(frozen=True)
class CaseResult:
    name: str
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


def execute(name: str, argv: list[str], env: dict[str, str]) -> CaseResult:
    proc = subprocess.run(
        argv,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CaseResult(name, argv, proc.returncode, proc.stdout, proc.stderr)


def assert_absent(value: str, texts: list[str]) -> None:
    for text in texts:
        if value in text:
            raise AssertionError("secret value crossed a public output boundary")


def main() -> None:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    events_file = WORK / "events.jsonl"
    valid_env = os.environ.copy()
    valid_env.update(
        {
            "DEMO_HOST": "127.0.0.1",
            "DEMO_PORT": "18080",
            "DEMO_LOG_LEVEL": "INFO",
            "DEMO_API_TOKEN": SECRET_VALUE,
        }
    )
    valid_argv = [
        sys.executable,
        str(APP),
        "--defaults",
        str(DEFAULTS),
        "--config",
        str(DEVELOPMENT),
        "--port",
        "19090",
        "--log-level",
        "DEBUG",
        "--events-file",
        str(events_file),
        "--run-id",
        "config-lab-run",
        "--dry-run",
    ]
    valid = execute("valid-precedence", valid_argv, valid_env)
    if valid.returncode != 0:
        raise AssertionError(valid.stderr)
    resolved = json.loads(valid.stdout)
    event_rows = [json.loads(line) for line in events_file.read_text(encoding="utf-8").splitlines()]

    assert resolved["status"] == "ok"
    assert resolved["mode"] == "dry_run"
    assert resolved["config"]["service_name"] == "config-log-demo"
    assert resolved["config"]["host"] == "127.0.0.1"
    assert resolved["config"]["port"] == 19090
    assert resolved["config"]["log_level"] == "DEBUG"
    assert resolved["sources"] == {
        "service_name": "defaults",
        "host": "env",
        "port": "cli",
        "log_level": "cli",
        "output_dir": "file",
    }
    assert resolved["secret_configured"] is True
    assert len(event_rows) == 4
    assert {row["event"] for row in event_rows} == {
        "config_resolved",
        "config_validated",
        "execution_planned",
        "run_complete",
    }
    assert {row["run_id"] for row in event_rows} == {"config-lab-run"}

    bad_unknown = WORK / "unknown.json"
    bad_unknown.write_text('{"unexpected": true}\n', encoding="utf-8")
    unknown = execute(
        "unknown-key",
        [
            sys.executable,
            str(APP),
            "--defaults",
            str(DEFAULTS),
            "--config",
            str(bad_unknown),
            "--dry-run",
        ],
        os.environ.copy(),
    )
    assert unknown.returncode == 2
    assert "unknown keys: unexpected" in unknown.stderr

    invalid_env = os.environ.copy()
    invalid_env["DEMO_PORT"] = "not-an-integer"
    invalid_port = execute(
        "invalid-port",
        [sys.executable, str(APP), "--defaults", str(DEFAULTS), "--dry-run"],
        invalid_env,
    )
    assert invalid_port.returncode == 2
    assert "port must be an integer" in invalid_port.stderr

    all_text = [
        valid.stdout,
        valid.stderr,
        events_file.read_text(encoding="utf-8"),
        unknown.stdout,
        unknown.stderr,
        invalid_port.stdout,
        invalid_port.stderr,
    ]
    assert_absent(SECRET_VALUE, all_text)

    (REPORTS / "resolved_config.json").write_text(
        json.dumps(resolved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    shutil.copyfile(events_file, REPORTS / "events.jsonl")
    report = {
        "precedence": "defaults<file<env<cli",
        "resolved": resolved,
        "event_count": len(event_rows),
        "event_names": [row["event"] for row in event_rows],
        "failure_cases": {
            "unknown_key_rc": unknown.returncode,
            "invalid_port_rc": invalid_port.returncode,
        },
        "secret_visible": False,
        "run_status": "ok",
        "cases": [
            asdict(valid) | {"stderr": "<4 JSONL events; see reports/events.jsonl>"},
            asdict(unknown),
            asdict(invalid_port),
        ],
    }
    (REPORTS / "config_log_probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    transcript = dedent(
        f"""
        # Project config and logging boundary transcript

        ## Valid precedence and dry-run

        ```bash
        DEMO_HOST=127.0.0.1 DEMO_PORT=18080 DEMO_LOG_LEVEL=INFO \\
        DEMO_API_TOKEN=<redacted> \\
        {shlex.join(valid_argv)}
        # rc={valid.returncode}
        ```

        Resolved public state:

        ```text
        CONFIG_PRECEDENCE=defaults<file<env<cli
        RESOLVED_HOST={resolved['config']['host']}
        RESOLVED_PORT={resolved['config']['port']}
        RESOLVED_LOG_LEVEL={resolved['config']['log_level']}
        SOURCE_SERVICE_NAME={resolved['sources']['service_name']}
        SOURCE_OUTPUT_DIR={resolved['sources']['output_dir']}
        SOURCE_HOST={resolved['sources']['host']}
        SOURCE_PORT={resolved['sources']['port']}
        LOG_EVENT_COUNT={len(event_rows)}
        SECRET_VISIBLE=no
        RUN_STATUS=ok
        ```

        ## Rejected unknown key

        ```text
        config error: config has unknown keys: unexpected
        UNKNOWN_KEY_RC={unknown.returncode}
        ```

        ## Rejected invalid port

        ```text
        config error: port must be an integer
        INVALID_PORT_RC={invalid_port.returncode}
        ```
        """
    ).lstrip()
    (REPORTS / "transcript.md").write_text(transcript, encoding="utf-8")

    summary = dedent(
        f"""
        # Config and logging lab summary

        - Precedence: `defaults < file < env < CLI`.
        - Resolved endpoint: `{resolved['config']['host']}:{resolved['config']['port']}`.
        - Resolved log level: `{resolved['config']['log_level']}`.
        - Structured events: `{len(event_rows)}` JSONL rows with one run id.
        - Unknown config key return code: `{unknown.returncode}`.
        - Invalid port return code: `{invalid_port.returncode}`.
        - Secret value visible in artifacts: `no`.
        - Dry-run status: `ok`.
        """
    ).lstrip()
    (REPORTS / "config_logging_summary.md").write_text(summary, encoding="utf-8")

    print("CONFIG_PRECEDENCE=defaults<file<env<cli")
    print(f"RESOLVED_HOST={resolved['config']['host']}")
    print(f"RESOLVED_PORT={resolved['config']['port']}")
    print(f"RESOLVED_LOG_LEVEL={resolved['config']['log_level']}")
    print(f"UNKNOWN_KEY_RC={unknown.returncode}")
    print(f"INVALID_PORT_RC={invalid_port.returncode}")
    print("SECRET_VISIBLE=no")
    print(f"LOG_EVENT_COUNT={len(event_rows)}")
    print("RUN_STATUS=ok")


if __name__ == "__main__":
    main()
