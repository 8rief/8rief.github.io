from __future__ import annotations

import argparse
import http.server
import ipaddress
import json
import os
import queue
import socket
import socketserver
import subprocess
import threading
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

HOST = "127.0.0.1"
PAYLOAD = b"network-foundations"


@dataclass
class TcpObservation:
    port: int
    sent: str
    received: str
    rtt_ms: float
    bytes_transferred: int
    throughput_mib_s: float


@dataclass
class UdpObservation:
    port: int
    sent: str
    received: str
    rtt_ms: float


@dataclass
class HttpObservation:
    port: int
    status: int
    content_type: str
    server_path: str
    body_contains: bool


def run_command(args: list[str], timeout: float = 4.0) -> str:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return f"command-not-found: {args[0]}\n"
    except subprocess.TimeoutExpired:
        return f"timeout: {' '.join(args)}\n"
    out = proc.stdout
    err = proc.stderr
    return (out + (("\n[stderr]\n" + err) if err else "")).strip() + "\n"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return "missing\n"


def parse_proc_net_dev(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines()[2:]:
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        fields = rest.split()
        if len(fields) < 16:
            continue
        rows.append({
            "name": name.strip(),
            "rx_bytes": int(fields[0]),
            "rx_packets": int(fields[1]),
            "tx_bytes": int(fields[8]),
            "tx_packets": int(fields[9]),
        })
    return rows


def linux_hex_ipv4(value: str) -> str:
    raw = bytes.fromhex(value)
    return socket.inet_ntoa(raw[::-1])


def route_mask_prefix(mask: str) -> int:
    return ipaddress.IPv4Network(f"0.0.0.0/{linux_hex_ipv4(mask)}").prefixlen


def parse_proc_net_route(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 8:
            continue
        iface, destination, gateway, flags, _refcnt, _use, _metric, mask = parts[:8]
        prefix = route_mask_prefix(mask)
        rows.append({
            "iface": iface,
            "destination": linux_hex_ipv4(destination),
            "gateway": linux_hex_ipv4(gateway),
            "flags_hex": flags,
            "mask": linux_hex_ipv4(mask),
            "prefix": prefix,
            "cidr": f"{linux_hex_ipv4(destination)}/{prefix}",
        })
    return rows


def choose_route(routes: list[dict[str, Any]], target_ip: str) -> dict[str, Any] | None:
    target = ipaddress.IPv4Address(target_ip)
    candidates: list[dict[str, Any]] = []
    for row in routes:
        network = ipaddress.IPv4Network(row["cidr"], strict=False)
        if target in network:
            candidates.append(row)
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: row["prefix"], reverse=True)[0]


def localhost_dns() -> list[dict[str, Any]]:
    answers = []
    for family, socktype, proto, canonname, sockaddr in socket.getaddrinfo("localhost", 0):
        answers.append({
            "family": socket.AddressFamily(family).name,
            "socktype": socket.SocketKind(socktype).name,
            "proto": proto,
            "canonname": canonname,
            "address": sockaddr[0],
        })
    # Keep deterministic ordering and remove duplicates.
    seen = set()
    unique = []
    for item in answers:
        key = tuple(item.items())
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        while True:
            data = self.request.recv(65536)
            if not data:
                break
            self.request.sendall(data.upper())


def observe_tcp() -> TcpObservation:
    with ThreadedTCPServer((HOST, 0), EchoHandler) as server:
        port = int(server.server_address[1])
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        start = time.perf_counter_ns()
        with socket.create_connection((HOST, port), timeout=2.0) as client:
            client.sendall(PAYLOAD)
            received = client.recv(1024)
        rtt_ms = (time.perf_counter_ns() - start) / 1_000_000

        block = b"x" * 65536
        total = 0
        start = time.perf_counter_ns()
        with socket.create_connection((HOST, port), timeout=2.0) as client:
            for _ in range(16):
                client.sendall(block)
                view = memoryview(bytearray(len(block)))
                got = 0
                while got < len(block):
                    n = client.recv_into(view[got:])
                    if n == 0:
                        raise RuntimeError("tcp echo closed early")
                    got += n
                total += got
        elapsed = max((time.perf_counter_ns() - start) / 1_000_000_000, 1e-9)
        server.shutdown()
        return TcpObservation(
            port=port,
            sent=PAYLOAD.decode(),
            received=received.decode(),
            rtt_ms=round(rtt_ms, 3),
            bytes_transferred=total,
            throughput_mib_s=round(total / (1024 * 1024) / elapsed, 3),
        )


def udp_server(sock: socket.socket, stop: threading.Event) -> None:
    sock.settimeout(0.1)
    while not stop.is_set():
        try:
            data, addr = sock.recvfrom(65535)
        except TimeoutError:
            continue
        sock.sendto(data.upper(), addr)


def observe_udp() -> UdpObservation:
    stop = threading.Event()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((HOST, 0))
        port = int(server.getsockname()[1])
        thread = threading.Thread(target=udp_server, args=(server, stop), daemon=True)
        thread.start()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.settimeout(2.0)
            start = time.perf_counter_ns()
            client.sendto(b"udp datagram", (HOST, port))
            data, _addr = client.recvfrom(65535)
            rtt_ms = (time.perf_counter_ns() - start) / 1_000_000
        stop.set()
        thread.join(timeout=1.0)
    return UdpObservation(port=port, sent="udp datagram", received=data.decode(), rtt_ms=round(rtt_ms, 3))


class JsonHTTPHandler(http.server.BaseHTTPRequestHandler):
    server_version = "NetFoundationsHTTP/1.0"

    def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
        body = json.dumps({"method": "GET", "path": self.path, "message": "hello network"}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *args: Any) -> None:
        return


def observe_http(reports: Path) -> HttpObservation:
    with http.server.ThreadingHTTPServer((HOST, 0), JsonHTTPHandler) as server:
        port = int(server.server_address[1])
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://{HOST}:{port}/hello?name=network"
        req = urllib.request.Request(url, headers={"User-Agent": "net-foundations-lab"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8")
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "curl_http.txt").write_text(run_command(["curl", "-sS", "-i", "--max-time", "2", url]), encoding="utf-8")
        (reports / "ss_listen.txt").write_text(run_command(["ss", "-ltn", f"sport = :{port}"]), encoding="utf-8")
        server.shutdown()
    return HttpObservation(port=port, status=status, content_type=content_type, server_path="/hello?name=network", body_contains="hello network" in body)


def collect(reports: Path) -> dict[str, Any]:
    reports.mkdir(parents=True, exist_ok=True)
    proc_dev = read_text(Path("/proc/net/dev"))
    proc_route = read_text(Path("/proc/net/route"))
    routes = parse_proc_net_route(proc_route)
    observations = {
        "environment": {
            "python": sys_version(),
            "platform": os.uname().sysname + " " + os.uname().release if hasattr(os, "uname") else "unknown",
        },
        "interfaces": parse_proc_net_dev(proc_dev),
        "routes": routes,
        "route_to_loopback": choose_route(routes, "127.0.0.1"),
        "route_to_example_address": choose_route(routes, "8.8.8.8"),
        "localhost_dns": localhost_dns(),
        "tcp": asdict(observe_tcp()),
        "udp": asdict(observe_udp()),
    }
    observations["http"] = asdict(observe_http(reports))
    (reports / "ip_addr.txt").write_text(run_command(["ip", "addr", "show"]), encoding="utf-8")
    (reports / "ip_route.txt").write_text(run_command(["ip", "route", "show"]), encoding="utf-8")
    (reports / "resolv_conf.txt").write_text(read_text(Path("/etc/resolv.conf")), encoding="utf-8")
    (reports / "getent_localhost.txt").write_text(run_command(["getent", "hosts", "localhost"]), encoding="utf-8")
    return observations


def sys_version() -> str:
    import sys
    return sys.version.split()[0]


def write_report(observations: dict[str, Any], reports: Path) -> None:
    tcp = observations["tcp"]
    udp = observations["udp"]
    http_obs = observations["http"]
    route = observations.get("route_to_example_address") or {}
    lines = [
        "# Computer Network Foundations Lab Report",
        "",
        f"- python: {observations['environment']['python']}",
        f"- platform: {observations['environment']['platform']}",
        f"- interfaces_observed: {len(observations['interfaces'])}",
        f"- routes_observed: {len(observations['routes'])}",
        f"- example_route_iface: {route.get('iface', 'missing')}",
        f"- localhost_dns_answers: {len(observations['localhost_dns'])}",
        f"- tcp_port: {tcp['port']}; rtt_ms: {tcp['rtt_ms']}; bytes: {tcp['bytes_transferred']}; throughput_mib_s: {tcp['throughput_mib_s']}",
        f"- udp_port: {udp['port']}; rtt_ms: {udp['rtt_ms']}; received: {udp['received']}",
        f"- http_port: {http_obs['port']}; status: {http_obs['status']}; content_type: {http_obs['content_type']}",
        "",
        "## Interpretation",
        "",
        "The lab stays on loopback for TCP, UDP, and HTTP so that it teaches network mechanics without scanning or touching external hosts. External-looking addresses are used only for local route-table selection, not for packets.",
    ]
    (reports / "network_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--reports", default="reports")
    args = parser.parse_args()
    reports = Path(args.reports)
    observations = collect(reports)
    (reports / "observations.json").write_text(json.dumps(observations, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(observations, reports)
    print(f"interfaces={len(observations['interfaces'])} routes={len(observations['routes'])}")
    print(f"localhost_dns_answers={len(observations['localhost_dns'])}")
    print(f"tcp_port={observations['tcp']['port']} tcp_echo={observations['tcp']['received']} tcp_bytes={observations['tcp']['bytes_transferred']} throughput_mib_s={observations['tcp']['throughput_mib_s']}")
    print(f"udp_port={observations['udp']['port']} udp_echo={observations['udp']['received']}")
    print(f"http_port={observations['http']['port']} http_status={observations['http']['status']} body_contains={observations['http']['body_contains']}")
    print("report=reports/network_report.md")


if __name__ == "__main__":
    main()
