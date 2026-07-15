# Project Test Pyramid and Regression Boundary Lab

This lab teaches how to choose the smallest useful test layer for a small data-processing project.

It uses only the Python standard library and demonstrates:

- unit tests for pure parsing/pricing rules;
- integration tests for a file-backed CSV -> JSON/JSONL pipeline;
- smoke tests for the CLI process boundary;
- a golden regression fixture that catches accidental output-contract changes;
- an invalid-input path that must fail without writing a misleading report.

Run:

```bash
bash run_lab.sh
```

Successful output includes:

```text
GOLDEN_REGRESSION_MATCH=yes
SUMMARY_NET_CENTS=14265
BAD_INPUT_RC=65
BAD_OUTPUT_EXISTS=no
RUN_STATUS=ok
```

Generated files are written under `reports/` and should not be committed.
