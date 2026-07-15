# Go Health Monitor Service

A small standard-library Go project used as a teaching capstone. It checks local HTTP targets, writes JSON/CSV reports, and exposes a local API for on-demand checks.

## Commands

```bash
./run_lab.sh
```

The lab starts a local demo target server on `127.0.0.1:18191`, builds `bin/healthmon`, runs tests, writes `reports/results.json` and `reports/results.csv`, then starts the monitor API on `127.0.0.1:18190`.

## Safety boundary

The sample configuration accepts only loopback hosts. This keeps the teaching lab local and avoids accidental scans of third-party services.
