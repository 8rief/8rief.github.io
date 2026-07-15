# Rust Log Insight CLI

A Rust teaching capstone for a reliable CLI plus local HTTP API. It parses local structured log lines, summarizes levels and services, writes JSON/CSV reports, and serves the same summary through an Axum API bound to `127.0.0.1`.

## Run

```bash
./run_lab.sh
```

The script runs format checks, tests, a CLI demo, and a local API smoke test. Generated evidence is written to `reports/`.

## Safety boundary

The API is a local teaching service. The default listen address is `127.0.0.1`, and the sample data is synthetic.
