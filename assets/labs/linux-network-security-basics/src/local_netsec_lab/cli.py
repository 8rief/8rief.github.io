from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from .command_boundary import evidence as command_evidence
from .hardening import build_static_report, fetch_header_report, write_json
from .server import serve_forever
from .service_map import map_ports, parse_ports, write_map


def path_boundary_evidence(base_url: str) -> dict[str, object]:
    unsafe_url = base_url.rstrip("/") + "/unsafe-file?name=../outside_area/private_note.txt"
    safe_url = base_url.rstrip("/") + "/safe-file?name=../outside_area/private_note.txt"
    public_url = base_url.rstrip("/") + "/safe-file?name=readme.txt"
    with urlopen(public_url, timeout=2.0) as resp:
        public_status = resp.status
        public_body = resp.read().decode("utf-8").strip()
    with urlopen(unsafe_url, timeout=2.0) as resp:
        unsafe_status = resp.status
        unsafe_body = resp.read().decode("utf-8").strip()
    try:
        with urlopen(safe_url, timeout=2.0) as resp:
            safe_status = resp.status
            safe_body = resp.read().decode("utf-8").strip()
    except HTTPError as exc:
        safe_status = exc.code
        safe_body = exc.read().decode("utf-8").strip()
    return {
        "public_file": {"status": public_status, "body": public_body},
        "unsafe_endpoint": {"status": unsafe_status, "body": unsafe_body},
        "safe_endpoint": {"status": safe_status, "body": safe_body},
        "boundary": "unsafe endpoint can leave document root; safe endpoint rejects the same lab-owned path",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Local-only Linux networking and security basics lab")
    sub = parser.add_subparsers(dest="command", required=True)

    server_p = sub.add_parser("server")
    server_p.add_argument("--host", default="127.0.0.1")
    server_p.add_argument("--port", type=int, default=18480)
    server_p.add_argument("--public-dir", type=Path, default=Path("sample_public"))
    server_p.add_argument("--outside-dir", type=Path, default=Path("outside_area"))

    map_p = sub.add_parser("map")
    map_p.add_argument("--host", default="127.0.0.1")
    map_p.add_argument("--ports", required=True)
    map_p.add_argument("--output", type=Path, required=True)

    path_p = sub.add_parser("path-boundary")
    path_p.add_argument("--base-url", required=True)
    path_p.add_argument("--output", type=Path, required=True)

    cmd_p = sub.add_parser("command-boundary")
    cmd_p.add_argument("--output", type=Path, required=True)

    hard_p = sub.add_parser("hardening")
    hard_p.add_argument("--base-url", required=True)
    hard_p.add_argument("--bind-host", default="127.0.0.1")
    hard_p.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "server":
        serve_forever(args.host, args.port, args.public_dir, args.outside_dir)
    elif args.command == "map":
        data = map_ports(args.host, parse_ports(args.ports))
        write_map(args.output, data)
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    elif args.command == "path-boundary":
        data = path_boundary_evidence(args.base_url)
        write_json(args.output, data)
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    elif args.command == "command-boundary":
        data = command_evidence()
        write_json(args.output, data)
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    elif args.command == "hardening":
        data = build_static_report(args.base_url, args.bind_host)
        data["runtime_headers"] = fetch_header_report(args.base_url)
        write_json(args.output, data)
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    else:
        raise AssertionError(args.command)


if __name__ == "__main__":
    main()
