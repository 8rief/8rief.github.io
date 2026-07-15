# Linux CLI and Shell Automation Lab

This lab builds a small, reproducible log-reporting workflow for zero-beginner Linux CLI and shell automation posts.

Run:

```bash
bash run_lab.sh
```

Expected visible outputs:

- `reports/transcript.txt`: command transcript and environment assumptions.
- `reports/summary.txt`: request count, error count, slow request count, and top status.
- `reports/status_counts.tsv`: status-code counts.
- `reports/path_latency.tsv`: average latency by path.
- `reports/batch-summary.tsv`: per-log-file line and error counts generated with safe `find -print0` handling.

The lab is deterministic and uses only Bash plus common GNU/Linux text tools.
