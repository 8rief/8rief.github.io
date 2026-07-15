from __future__ import annotations

import json
import socket
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from local_netsec_lab.command_boundary import validate_and_run
from local_netsec_lab.path_safety import PathBoundaryError, safe_resolve, unsafe_join
from local_netsec_lab.server import make_server
from local_netsec_lab.service_map import map_ports, parse_ports, probe_port, validate_loopback_host

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "sample_public"
OUTSIDE = ROOT / "outside_area"


class PathSafetyTests(unittest.TestCase):
    def test_safe_resolve_allows_public_file(self) -> None:
        resolved = safe_resolve(PUBLIC, "nested/info.txt")
        self.assertEqual(resolved.name, "info.txt")
        self.assertIn(PUBLIC.resolve(), resolved.parents)

    def test_safe_resolve_rejects_escape(self) -> None:
        with self.assertRaises(PathBoundaryError):
            safe_resolve(PUBLIC, "../outside_area/private_note.txt")

    def test_unsafe_join_can_escape(self) -> None:
        escaped = unsafe_join(PUBLIC, "../outside_area/private_note.txt").resolve()
        self.assertEqual(escaped, (OUTSIDE / "private_note.txt").resolve())


class CommandBoundaryTests(unittest.TestCase):
    def test_loopback_literal_is_accepted(self) -> None:
        result = validate_and_run("127.0.0.1")
        self.assertTrue(result.accepted)
        self.assertIn("loopback=127.0.0.1", result.output or "")

    def test_shell_metacharacters_are_rejected(self) -> None:
        result = validate_and_run("127.0.0.1; echo bad")
        self.assertFalse(result.accepted)
        self.assertEqual(result.argv, [])


class ServiceMapTests(unittest.TestCase):
    def test_parse_ports_limited_and_sorted(self) -> None:
        self.assertEqual(parse_ports("18480,18479-18481"), [18479, 18480, 18481])

    def test_non_loopback_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_loopback_host("192.0.2.10")

    def test_ipv6_loopback_probe_uses_address_family_resolution(self) -> None:
        try:
            listener = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            listener.bind(("::1", 0))
            listener.listen(2)
        except OSError as exc:
            self.skipTest(f"IPv6 loopback is unavailable: {exc}")

        port = listener.getsockname()[1]

        def serve_two_connections() -> None:
            try:
                for index in range(2):
                    conn, _ = listener.accept()
                    with conn:
                        if index == 1:
                            conn.recv(4096)
                            conn.sendall(b"HTTP/1.0 200 OK\r\nContent-Length: 0\r\n\r\n")
            finally:
                listener.close()

        thread = threading.Thread(target=serve_two_connections, daemon=True)
        thread.start()
        observation = probe_port("::1", port, timeout=1.0)
        thread.join(timeout=2.0)

        self.assertFalse(thread.is_alive())
        self.assertTrue(observation.open)
        self.assertEqual(observation.service_hint, "http-health")


class HttpServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server("127.0.0.1", 0, PUBLIC, OUTSIDE)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_headers(self) -> None:
        with urlopen(self.base_url + "/health", timeout=2.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(resp.status, 200)
            self.assertEqual(body["status"], "ok")
            self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")

    def test_safe_and_unsafe_path_endpoints(self) -> None:
        with urlopen(self.base_url + "/unsafe-file?name=../outside_area/private_note.txt", timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("outside the public document root", resp.read().decode("utf-8"))
        with self.assertRaises(HTTPError) as cm:
            urlopen(self.base_url + "/safe-file?name=../outside_area/private_note.txt", timeout=2.0)
        self.assertEqual(cm.exception.code, 400)
        with self.assertRaises(HTTPError) as encoded:
            urlopen(
                self.base_url + "/safe-file?name=%2e%2e%2foutside_area%2fprivate_note.txt",
                timeout=2.0,
            )
        self.assertEqual(encoded.exception.code, 400)

    def test_post_returns_method_not_allowed(self) -> None:
        req = Request(self.base_url + "/health", data=b"x", method="POST")
        with self.assertRaises(HTTPError) as cm:
            urlopen(req, timeout=2.0)
        self.assertEqual(cm.exception.code, 405)
        self.assertEqual(cm.exception.headers.get("Allow"), "GET, HEAD")

    def test_service_map_finds_open_port(self) -> None:
        data = map_ports("127.0.0.1", [self.server.server_port])
        self.assertEqual(data["open_ports"], [self.server.server_port])
        self.assertEqual(data["observations"][0]["service_hint"], "http-health")


if __name__ == "__main__":
    unittest.main()
