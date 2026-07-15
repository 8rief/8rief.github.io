# C++ File Indexer Service

A C++ teaching capstone that uses CMake plus mainstream libraries to build a local file indexer CLI and HTTP API.

## Run

```bash
./run_lab.sh
```

The script configures with Ninja, fetches pinned third-party libraries, builds, runs CTest, runs the CLI scan demo, and starts a local HTTP API on `127.0.0.1:18280` for smoke checks.

## Safety boundary

The project scans only the sample local directory by default and serves only on loopback.
