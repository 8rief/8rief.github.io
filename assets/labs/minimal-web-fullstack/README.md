# Minimal Web Full-stack Lab

A zero-dependency local Web project for teaching the minimum full-stack loop:

- browser page: `public/index.html`, `public/styles.css`, `public/app.js`
- local HTTP/API server: `server.mjs`
- persistence: JSON file at `data/tasks.json` or `TASKS_DATA_FILE`
- verification: Node's built-in test runner plus a smoke script that starts the server and calls the real API

Run the complete lab:

```bash
bash run_lab.sh
```

Visible outputs:

- `reports/transcript.txt`: command transcript and environment assumptions.
- `reports/smoke-report.json`: API smoke result.
- `reports/api-transcript.ndjson`: request/status transcript.
- `.lab_tmp/data/tasks.json`: persisted task data after the smoke run.

Run the app manually:

```bash
node scripts/reset-data.mjs data/tasks.json
node server.mjs
```

Then open `http://127.0.0.1:3000`.
