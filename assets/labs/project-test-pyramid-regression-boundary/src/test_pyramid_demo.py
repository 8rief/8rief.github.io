#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EXIT_INPUT_ERROR = 65


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    customer: str
    item: str
    unit_price_cents: int
    quantity: int
    discount_pct: int

    @property
    def gross_cents(self) -> int:
        return self.unit_price_cents * self.quantity

    @property
    def discount_cents(self) -> int:
        return (self.gross_cents * self.discount_pct + 50) // 100

    @property
    def net_cents(self) -> int:
        return self.gross_cents - self.discount_cents


def parse_order_row(row: dict[str, str], line_number: int) -> OrderLine:
    required = ["order_id", "customer", "item", "unit_price_cents", "quantity", "discount_pct"]
    missing = [name for name in required if not row.get(name, "").strip()]
    if missing:
        raise ValueError(f"line {line_number}: missing fields {','.join(missing)}")
    try:
        unit_price_cents = int(row["unit_price_cents"])
        quantity = int(row["quantity"])
        discount_pct = int(row["discount_pct"])
    except ValueError as exc:
        raise ValueError(f"line {line_number}: numeric fields must be integers") from exc
    if unit_price_cents < 0:
        raise ValueError(f"line {line_number}: unit_price_cents must be >= 0")
    if quantity <= 0:
        raise ValueError(f"line {line_number}: quantity must be > 0")
    if not 0 <= discount_pct <= 100:
        raise ValueError(f"line {line_number}: discount_pct must be between 0 and 100")
    return OrderLine(
        order_id=row["order_id"].strip(),
        customer=row["customer"].strip(),
        item=row["item"].strip(),
        unit_price_cents=unit_price_cents,
        quantity=quantity,
        discount_pct=discount_pct,
    )


def load_orders(path: Path) -> list[OrderLine]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [parse_order_row(row, index) for index, row in enumerate(reader, start=2)]


def summarize_orders(lines: Iterable[OrderLine]) -> dict[str, int | str]:
    materialized = list(lines)
    customer_totals: dict[str, int] = {}
    order_ids: set[str] = set()
    gross = 0
    discount = 0
    for line in materialized:
        gross += line.gross_cents
        discount += line.discount_cents
        order_ids.add(line.order_id)
        customer_totals[line.customer] = customer_totals.get(line.customer, 0) + line.net_cents
    top_customer = ""
    top_customer_net = 0
    if customer_totals:
        top_customer, top_customer_net = sorted(customer_totals.items(), key=lambda item: (-item[1], item[0]))[0]
    return {
        "line_count": len(materialized),
        "order_count": len(order_ids),
        "gross_cents": gross,
        "total_discount_cents": discount,
        "net_cents": gross - discount,
        "top_customer": top_customer,
        "top_customer_net_cents": top_customer_net,
        "rejected_lines": 0,
    }


def write_json(path: Path, payload: dict[str, int | str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_event(path: Path, event: dict[str, int | str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def run_pipeline(input_path: Path, output_path: Path, log_path: Path) -> dict[str, int | str]:
    append_event(log_path, {"event": "start", "input": str(input_path)})
    orders = load_orders(input_path)
    append_event(log_path, {"event": "loaded", "line_count": len(orders)})
    summary = summarize_orders(orders)
    write_json(output_path, summary)
    append_event(log_path, {"event": "summary_written", "net_cents": int(summary["net_cents"])})
    return summary


def compare_golden(actual_path: Path, expected_path: Path) -> tuple[bool, list[str]]:
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    diffs = []
    for key in sorted(set(actual) | set(expected)):
        if actual.get(key) != expected.get(key):
            diffs.append(f"{key}: expected {expected.get(key)!r}, got {actual.get(key)!r}")
    return not diffs, diffs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a small order summary pipeline for test-pyramid teaching.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--golden", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run_pipeline(args.input, args.output, args.log)
        golden_ok = "not_checked"
        if args.golden is not None:
            ok, diffs = compare_golden(args.output, args.golden)
            golden_ok = "yes" if ok else "no"
            if not ok:
                print("golden_mismatch=" + "; ".join(diffs), file=sys.stderr)
                return 1
        print(
            "PIPELINE_OK "
            f"lines={summary['line_count']} orders={summary['order_count']} "
            f"gross_cents={summary['gross_cents']} net_cents={summary['net_cents']} "
            f"top_customer={summary['top_customer']} golden={golden_ok}"
        )
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
