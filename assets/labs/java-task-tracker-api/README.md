# Java Task Tracker API

A teaching capstone for Java from zero to a runnable project.

It contains:

- domain records and enums;
- a service layer with validation and invariants;
- JSON file persistence with Jackson;
- CSV export;
- a small command-line interface;
- a Spring Boot REST API;
- JUnit and MockMvc tests;
- a reproducible lab script and transcript.

Run:

```bash
./run_lab.sh
```

The script bootstraps a local JDK/Maven if system tools are missing, runs tests, builds the jar, runs CLI commands, starts the API on `127.0.0.1`, executes curl smoke checks, and writes `reports/transcript.txt`.
