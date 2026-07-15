# Linux Networking And Authorized Security Basics Lab

This is a local-only teaching lab. All network commands target `127.0.0.1`, and the intentionally unsafe endpoint reads only lab-owned files so the reader can compare unsafe and safe path handling.

Run the full lab:

```bash
./run_lab.sh
```

Main artifacts:

- `reports/transcript.txt`: command transcript and expected observations.
- `reports/health.json`: local HTTP service health response.
- `reports/curl_health_verbose.txt`: `curl -v` request/response trace.
- `reports/service_map.json`: constrained loopback port map.
- `reports/path_boundary.json`: unsafe vs safe path handling evidence.
- `reports/command_boundary.json`: subprocess input-validation evidence.
- `reports/hardening_report.json`: local service hardening checklist.
