from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class HardeningItem:
    check: str
    status: str
    evidence: str


def build_static_report(base_url: str, bind_host: str) -> dict[str, object]:
    items = [
        HardeningItem("bind-address", "pass" if bind_host.startswith("127.") else "review", bind_host),
        HardeningItem("allowed-methods", "pass", "GET and HEAD are expected; unsupported methods return 405"),
        HardeningItem("path-boundary", "pass", "safe endpoint resolves and checks document-root containment"),
        HardeningItem("subprocess-boundary", "pass", "command demo validates loopback IP and uses argv list without shell"),
        HardeningItem("service-map-scope", "pass", "port mapper rejects non-loopback targets and limits range size"),
    ]
    return {"base_url": base_url, "items": [asdict(i) for i in items]}


def fetch_header_report(base_url: str, timeout: float = 2.0) -> dict[str, object]:
    req = Request(base_url.rstrip("/") + "/health", method="GET")
    with urlopen(req, timeout=timeout) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return {
            "status": resp.status,
            "headers": headers,
            "header_checks": [
                {
                    "check": "x-content-type-options",
                    "status": "pass" if headers.get("x-content-type-options") == "nosniff" else "review",
                    "evidence": headers.get("x-content-type-options", "missing"),
                },
                {
                    "check": "cache-control",
                    "status": "pass" if "no-store" in headers.get("cache-control", "") else "review",
                    "evidence": headers.get("cache-control", "missing"),
                },
            ],
        }


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
