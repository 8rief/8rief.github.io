#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "test_pyramid_demo.py"
REPORTS = ROOT / "reports"


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def write_bad_input(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["order_id", "customer", "item", "unit_price_cents", "quantity", "discount_pct"])
        writer.writerow(["bad-1", "alice", "pen", "120", "0", "0"])


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    summary_path = REPORTS / "summary.json"
    log_path = REPORTS / "events.jsonl"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--input",
        str(ROOT / "data" / "orders.csv"),
        "--output",
        str(summary_path),
        "--log",
        str(log_path),
        "--golden",
        str(ROOT / "fixtures" / "golden_summary.json"),
    ]
    success = run_command(cmd)
    bad_input = REPORTS / "bad_orders.csv"
    bad_output = REPORTS / "bad_summary.json"
    bad_log = REPORTS / "bad_events.jsonl"
    write_bad_input(bad_input)
    bad = run_command([sys.executable, str(SCRIPT), "--input", str(bad_input), "--output", str(bad_output), "--log", str(bad_log)])
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    event_count = len(log_path.read_text(encoding="utf-8").splitlines())
    probe = {
        "unit_layer": "covered_by_unittest_discovery",
        "integration_layer": "file_pipeline_and_jsonl_events",
        "smoke_layer": "cli_subprocess_exit_and_marker",
        "regression_layer": "golden_summary_json",
        "success_rc": success.returncode,
        "success_stdout": success.stdout.strip(),
        "bad_input_rc": bad.returncode,
        "bad_input_stderr": bad.stderr.strip(),
        "summary": summary,
        "event_count": event_count,
        "bad_output_exists": bad_output.exists(),
    }
    (REPORTS / "test_pyramid_probe.json").write_text(json.dumps(probe, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (REPORTS / "test_pyramid_report.md").write_text(
        "# Test pyramid probe\n\n"
        f"- success command rc: `{success.returncode}`\n"
        f"- success marker: `{success.stdout.strip()}`\n"
        f"- bad input rc: `{bad.returncode}`\n"
        f"- bad input stderr: `{bad.stderr.strip()}`\n"
        f"- line count: `{summary['line_count']}`\n"
        f"- net cents: `{summary['net_cents']}`\n"
        f"- top customer: `{summary['top_customer']}`\n"
        f"- JSONL events: `{event_count}`\n",
        encoding="utf-8",
    )
    print("UNIT_LAYER=unittest")
    print("INTEGRATION_LAYER=file_pipeline")
    print("SMOKE_LAYER=cli_subprocess")
    print("GOLDEN_REGRESSION_MATCH=yes" if success.returncode == 0 else "GOLDEN_REGRESSION_MATCH=no")
    print(f"SUMMARY_LINE_COUNT={summary['line_count']}")
    print(f"SUMMARY_NET_CENTS={summary['net_cents']}")
    print(f"SUMMARY_TOP_CUSTOMER={summary['top_customer']}")
    print(f"JSONL_EVENT_COUNT={event_count}")
    print(f"BAD_INPUT_RC={bad.returncode}")
    print(f"BAD_OUTPUT_EXISTS={'yes' if bad_output.exists() else 'no'}")
    ok = success.returncode == 0 and bad.returncode == 65 and not bad_output.exists() and summary["net_cents"] == 14265
    print(f"RUN_STATUS={'ok' if ok else 'fail'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
