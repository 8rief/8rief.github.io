# Computer Network Foundations Lab

A non-security, Linux-first network foundations lab. It records local interface and route evidence, resolver behavior for localhost, TCP byte-stream behavior, UDP datagram behavior, HTTP request/response evidence, and loopback timing/throughput observations.

Run:

```bash
bash run_lab.sh
```

Generated artifacts:

- `reports/transcript.txt`: full command transcript.
- `reports/observations.json`: machine-readable observations.
- `reports/network_report.md`: human-readable report.
- `reports/ip_addr.txt`, `reports/ip_route.txt`, `reports/resolv_conf.txt`: Linux environment evidence.
- `reports/curl_http.txt`, `reports/ss_listen.txt`: local service evidence when tools are available.
- `.lab_tmp/`: generated temporary files, recreated by `run_lab.sh`.
