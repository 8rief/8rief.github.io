from __future__ import annotations

import json
from http.client import HTTPConnection, HTTPException
import socket
import time
from dataclasses import asdict, dataclass
from pathlib import Path

LOOPBACK_NAMES = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True)
class PortObservation:
    host: str
    port: int
    open: bool
    latency_ms: float
    service_hint: str


def parse_ports(spec: str, limit: int = 128) -> list[int]:
    ports: list[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_s, end_s = chunk.split("-", 1)
            start, end = int(start_s), int(end_s)
            if start > end:
                raise ValueError("port range start must not exceed end")
            ports.extend(range(start, end + 1))
        else:
            ports.append(int(chunk))
    unique = sorted(set(ports))
    if not unique:
        raise ValueError("at least one port is required")
    if len(unique) > limit:
        raise ValueError(f"port list is limited to {limit} entries")
    if any(p < 1 or p > 65535 for p in unique):
        raise ValueError("ports must be between 1 and 65535")
    return unique


def validate_loopback_host(host: str) -> str:
    if host not in LOOPBACK_NAMES:
        raise ValueError("this lab only maps loopback hosts")
    return host


def probe_port(host: str, port: int, timeout: float = 0.25) -> PortObservation:
    validate_loopback_host(host)
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            is_open = True
    except OSError:
        is_open = False
    elapsed_ms = (time.perf_counter() - start) * 1000
    hint = "closed"
    if is_open:
        hint = "tcp-open"
        connection = HTTPConnection(host, port, timeout=timeout)
        try:
            connection.request("GET", "/health", headers={"User-Agent": "local-netsec-lab"})
            response = connection.getresponse()
            if response.status == 200:
                hint = "http-health"
        except (OSError, HTTPException):
            hint = "tcp-open"
        finally:
            connection.close()
    return PortObservation(host=host, port=port, open=is_open, latency_ms=round(elapsed_ms, 3), service_hint=hint)


def map_ports(host: str, ports: list[int], timeout: float = 0.25) -> dict[str, object]:
    validate_loopback_host(host)
    observations = [probe_port(host, p, timeout=timeout) for p in ports]
    return {
        "host": host,
        "scope": "loopback-only",
        "open_ports": [o.port for o in observations if o.open],
        "observations": [asdict(o) for o in observations],
    }


def write_map(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
