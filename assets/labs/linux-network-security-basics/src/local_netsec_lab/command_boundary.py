from __future__ import annotations

import ipaddress
import json
import subprocess
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CommandValidation:
    value: str
    accepted: bool
    reason: str
    argv: list[str]
    output: str | None = None


def build_safe_probe_argv(value: str) -> list[str]:
    """Build an argument-list command after strict loopback-IP validation."""

    try:
        ip = ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValueError("value must be an IP literal") from exc
    if not ip.is_loopback:
        raise ValueError("only loopback targets are allowed in this lab")
    return [sys.executable, "-c", "import sys; print('loopback=' + sys.argv[1])", str(ip)]


def validate_and_run(value: str) -> CommandValidation:
    try:
        argv = build_safe_probe_argv(value)
    except ValueError as exc:
        return CommandValidation(value=value, accepted=False, reason=str(exc), argv=[])
    completed = subprocess.run(argv, check=True, text=True, capture_output=True, timeout=2.0)
    return CommandValidation(
        value=value,
        accepted=True,
        reason="accepted loopback IP literal and executed without shell",
        argv=argv,
        output=completed.stdout.strip(),
    )


def evidence() -> dict[str, object]:
    safe = validate_and_run("127.0.0.1")
    rejected = validate_and_run("127.0.0.1; echo bad")
    return {"safe": asdict(safe), "rejected": asdict(rejected)}


def evidence_json() -> str:
    return json.dumps(evidence(), ensure_ascii=False, indent=2, sort_keys=True)
