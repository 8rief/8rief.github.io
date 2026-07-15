from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src import netlab


class NetlabTests(unittest.TestCase):
    def test_linux_hex_ipv4(self) -> None:
        self.assertEqual(netlab.linux_hex_ipv4("0100007F"), "127.0.0.1")
        self.assertEqual(netlab.linux_hex_ipv4("00000000"), "0.0.0.0")

    def test_choose_longest_prefix_route(self) -> None:
        routes = [
            {"cidr": "0.0.0.0/0", "iface": "default", "prefix": 0},
            {"cidr": "10.1.0.0/16", "iface": "private16", "prefix": 16},
            {"cidr": "10.1.2.0/24", "iface": "private24", "prefix": 24},
        ]
        self.assertEqual(netlab.choose_route(routes, "10.1.2.3")["iface"], "private24")
        self.assertEqual(netlab.choose_route(routes, "10.1.9.3")["iface"], "private16")
        self.assertEqual(netlab.choose_route(routes, "8.8.8.8")["iface"], "default")

    def test_parse_proc_net_dev(self) -> None:
        text = "Inter-| Receive | Transmit\n face |bytes packets errs drop fifo frame compressed multicast|bytes packets errs drop fifo colls carrier compressed\n lo: 10 1 0 0 0 0 0 0 20 2 0 0 0 0 0 0\n"
        rows = netlab.parse_proc_net_dev(text)
        self.assertEqual(rows[0]["name"], "lo")
        self.assertEqual(rows[0]["rx_bytes"], 10)
        self.assertEqual(rows[0]["tx_packets"], 2)

    def test_tcp_udp_http_observations(self) -> None:
        tcp = netlab.observe_tcp()
        self.assertEqual(tcp.received, "NETWORK-FOUNDATIONS")
        self.assertGreater(tcp.bytes_transferred, 0)
        udp = netlab.observe_udp()
        self.assertEqual(udp.received, "UDP DATAGRAM")
        with tempfile.TemporaryDirectory() as td:
            http = netlab.observe_http(Path(td))
            self.assertEqual(http.status, 200)
            self.assertTrue(http.body_contains)
            self.assertTrue((Path(td) / "curl_http.txt").exists())

    def test_collect_writes_report_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            reports = Path(td)
            observations = netlab.collect(reports)
            self.assertIn("interfaces", observations)
            self.assertIn("routes", observations)
            self.assertTrue((reports / "curl_http.txt").exists())
            self.assertTrue((reports / "ss_listen.txt").exists())


if __name__ == "__main__":
    unittest.main()
