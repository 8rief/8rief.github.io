# Local Evidence Kit

This teaching project turns a small file-scanning script into a reusable Python package with:

- a deterministic file manifest builder;
- JSON and CSV export;
- a Typer CLI;
- a local FastAPI application;
- an HTTP client wrapper;
- pytest coverage for pure logic, CLI, API, and client boundaries.

## Run

```bash
./run_lab.sh
```

The script creates a virtual environment, installs the package in editable mode, runs tests, executes the CLI, and writes a transcript to `reports/transcript.txt`.
