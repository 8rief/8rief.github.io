# Data Processing and Visualization Lab

A Python standard-library lab for the data-processing and visualization teaching package.

Run:

```bash
bash run_lab.sh
```

Visible outputs:

- `data/raw/sales.csv`: deterministic raw CSV with valid and invalid rows.
- `data/processed/clean_sales.csv`: validated rows with computed revenue.
- `data/processed/rejected_sales.csv`: rejected rows and reasons.
- `data/processed/sales.sqlite3`: SQLite database used for summaries.
- `reports/summary.json`: machine-readable summary.
- `reports/region_revenue.svg`: visible bar chart.
- `reports/report.md`: human-readable report.
- `reports/transcript.txt`: reproducible command transcript.
