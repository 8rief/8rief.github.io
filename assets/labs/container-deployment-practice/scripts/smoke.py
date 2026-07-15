#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.request import urlopen


def get_json(url: str) -> dict:
    with urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return {"status_code": response.status, "payload": payload}


def wait_health(base_url: str, attempts: int = 30) -> dict:
    last_error = ""
    for _ in range(attempts):
        try:
            result = get_json(f"{base_url}/health")
            if result["status_code"] == 200 and result["payload"].get("status") == "ok":
                return result
        except Exception as exc:  # local smoke diagnostic only
            last_error = repr(exc)
        time.sleep(1)
    raise RuntimeError(f"health check failed: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the container deployment lab service.")
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--label", default="smoke")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    health = wait_health(args.base_url)
    first = get_json(f"{args.base_url}/visits?label={args.label}-one")
    second = get_json(f"{args.base_url}/visits?label={args.label}-two")
    state = get_json(f"{args.base_url}/state")
    config = get_json(f"{args.base_url}/config")
    payload = {
        "base_url": args.base_url,
        "health": health,
        "first_visit": first,
        "second_visit": second,
        "state": state,
        "config": config,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"health_status={health['payload']['status']}")
    print(f"app_name={health['payload']['app']}")
    print(f"visits_after_smoke={state['payload']['visits']}")
    print(f"event_count={state['payload']['event_count']}")
    print(f"smoke_report={args.out}")


if __name__ == "__main__":
    main()
