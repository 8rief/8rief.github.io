#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.sax.saxutils import escape

RAW_ROWS = [
    ("A001", "2026-01-03", "North", "Web", "Notebook", "2", "12.50", "0.10"),
    ("A002", "2026-01-04", "South", "Store", "Pen", "10", "1.20", "0"),
    ("A003", "2026-01-05", "East", "Web", "Backpack", "1", "45.00", "0.05"),
    ("A004", "2026-01-06", "West", "Store", "Notebook", "3", "12.50", "0"),
    ("A005", "2026-01-07", "North", "Web", "Pen", "20", "1.20", "0.05"),
    ("A006", "2026-01-08", "South", "Web", "Backpack", "2", "45.00", "0.10"),
    ("A007", "2026-02-02", "East", "Store", "Notebook", "4", "12.50", "0"),
    ("A008", "2026-02-03", "West", "Web", "Pen", "30", "1.20", "0"),
    ("A009", "2026-02-04", "North", "Store", "Backpack", "1", "45.00", "0"),
    ("A010", "2026-02-05", "South", "Store", "Notebook", "5", "12.50", "0.10"),
    ("A011", "2026-02-06", "East", "Web", "Pen", "25", "1.20", "0.05"),
    ("A012", "2026-02-07", "West", "Store", "Backpack", "2", "45.00", "0.05"),
    ("A013", "2026-03-01", "North", "Web", "Notebook", "6", "12.50", "0"),
    ("A014", "2026-03-02", "South", "Web", "Pen", "40", "1.20", "0"),
    ("A015", "2026-03-03", "East", "Store", "Backpack", "2", "45.00", "0.10"),
    ("A016", "2026-03-04", "West", "Web", "Notebook", "1", "12.50", "0"),
    ("A017", "2026-03-05", "", "Web", "Notebook", "2", "12.50", "0"),
    ("A018", "2026-03-06", "North", "Store", "Pen", "-2", "1.20", "0"),
    ("A019", "2026-13-01", "East", "Web", "Backpack", "1", "45.00", "0"),
    ("A010", "2026-03-07", "South", "Web", "Notebook", "1", "12.50", "0"),
]

FIELDNAMES = ["order_id", "date", "region", "channel", "product", "units", "unit_price", "discount_pct"]
CLEAN_FIELDS = FIELDNAMES + ["revenue"]
REJECT_FIELDS = FIELDNAMES + ["reason"]
TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class CleanRow:
    order_id: str
    date: str
    region: str
    channel: str
    product: str
    units: int
    unit_price: Decimal
    discount_pct: Decimal
    revenue: Decimal

    def as_csv_row(self) -> dict[str, str]:
        return {
            "order_id": self.order_id,
            "date": self.date,
            "region": self.region,
            "channel": self.channel,
            "product": self.product,
            "units": str(self.units),
            "unit_price": money(self.unit_price),
            "discount_pct": str(self.discount_pct),
            "revenue": money(self.revenue),
        }


def money(value: Decimal | float | int | str) -> str:
    decimal = value if isinstance(value, Decimal) else Decimal(str(value))
    return str(decimal.quantize(TWOPLACES, rounding=ROUND_HALF_UP))


def generate_raw_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDNAMES)
        writer.writerows(RAW_ROWS)


def parse_decimal(value: str, field: str) -> Decimal:
    try:
        return Decimal(value)
    except Exception as exc:  # Decimal raises multiple concrete exceptions.
        raise ValueError(f"{field} is not a decimal") from exc


def validate_row(row: dict[str, str], seen_ids: set[str]) -> tuple[CleanRow | None, str | None]:
    order_id = (row.get("order_id") or "").strip()
    if not order_id:
        return None, "missing_order_id"
    if order_id in seen_ids:
        return None, "duplicate_order_id"

    raw_date = (row.get("date") or "").strip()
    try:
        parsed_date = date.fromisoformat(raw_date)
    except ValueError:
        return None, "invalid_date"

    region = (row.get("region") or "").strip()
    channel = (row.get("channel") or "").strip()
    product = (row.get("product") or "").strip()
    if not region:
        return None, "missing_region"
    if channel not in {"Web", "Store"}:
        return None, "invalid_channel"
    if not product:
        return None, "missing_product"

    try:
        units = int((row.get("units") or "").strip())
    except ValueError:
        return None, "invalid_units"
    if units <= 0:
        return None, "invalid_units"

    try:
        unit_price = parse_decimal((row.get("unit_price") or "").strip(), "unit_price")
        discount_pct = parse_decimal((row.get("discount_pct") or "").strip(), "discount_pct")
    except ValueError as exc:
        return None, str(exc)
    if unit_price <= 0:
        return None, "invalid_unit_price"
    if discount_pct < 0 or discount_pct >= 1:
        return None, "invalid_discount_pct"

    seen_ids.add(order_id)
    revenue = (Decimal(units) * unit_price * (Decimal("1") - discount_pct)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return CleanRow(order_id, parsed_date.isoformat(), region, channel, product, units, unit_price, discount_pct, revenue), None


def clean_csv(raw_path: Path, clean_path: Path, reject_path: Path) -> tuple[list[CleanRow], list[dict[str, str]]]:
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    reject_path.parent.mkdir(parents=True, exist_ok=True)
    clean_rows: list[CleanRow] = []
    rejects: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    with raw_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean, reason = validate_row(row, seen_ids)
            if clean is None:
                rejected = {field: row.get(field, "") for field in FIELDNAMES}
                rejected["reason"] = reason or "unknown"
                rejects.append(rejected)
            else:
                clean_rows.append(clean)

    with clean_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CLEAN_FIELDS)
        writer.writeheader()
        writer.writerows(row.as_csv_row() for row in clean_rows)
    with reject_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REJECT_FIELDS)
        writer.writeheader()
        writer.writerows(rejects)
    return clean_rows, rejects


def build_database(db_path: Path, rows: list[CleanRow]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE sales (
                order_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                month TEXT NOT NULL,
                region TEXT NOT NULL,
                channel TEXT NOT NULL,
                product TEXT NOT NULL,
                units INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                discount_pct REAL NOT NULL,
                revenue REAL NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO sales(order_id, date, month, region, channel, product, units, unit_price, discount_pct, revenue)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.order_id,
                    row.date,
                    row.date[:7],
                    row.region,
                    row.channel,
                    row.product,
                    row.units,
                    float(row.unit_price),
                    float(row.discount_pct),
                    float(row.revenue),
                )
                for row in rows
            ],
        )
        conn.commit()


def query_pairs(conn: sqlite3.Connection, sql: str) -> list[dict[str, object]]:
    cur = conn.execute(sql)
    names = [item[0] for item in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def build_summary(db_path: Path, raw_count: int, clean_count: int, reject_count: int) -> dict[str, object]:
    with sqlite3.connect(db_path) as conn:
        total = conn.execute("SELECT ROUND(SUM(revenue), 2), SUM(units) FROM sales").fetchone()
        by_region = query_pairs(conn, "SELECT region, ROUND(SUM(revenue), 2) AS revenue FROM sales GROUP BY region ORDER BY revenue DESC, region")
        by_month = query_pairs(conn, "SELECT month, ROUND(SUM(revenue), 2) AS revenue FROM sales GROUP BY month ORDER BY month")
        by_product = query_pairs(conn, "SELECT product, ROUND(SUM(revenue), 2) AS revenue FROM sales GROUP BY product ORDER BY revenue DESC, product")
        by_channel = query_pairs(conn, "SELECT channel, ROUND(SUM(revenue), 2) AS revenue FROM sales GROUP BY channel ORDER BY revenue DESC, channel")
    return {
        "raw_rows": raw_count,
        "clean_rows": clean_count,
        "rejected_rows": reject_count,
        "total_units": int(total[1]),
        "total_revenue": float(total[0]),
        "by_region": by_region,
        "by_month": by_month,
        "by_product": by_product,
        "by_channel": by_channel,
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_region_svg(path: Path, by_region: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 760, 420
    margin_left, margin_bottom, chart_top = 90, 70, 52
    chart_width, chart_height = 600, 270
    max_value = max(float(item["revenue"]) for item in by_region)
    bar_gap = 26
    bar_width = (chart_width - bar_gap * (len(by_region) - 1)) / len(by_region)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Revenue by region</title>',
        '<desc id="desc">A bar chart showing revenue by region after CSV cleaning and SQLite aggregation.</desc>',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif}.title{font-size:22px;font-weight:700;fill:#0f172a}.axis{stroke:#475569;stroke-width:1.5}.grid{stroke:#e2e8f0}.label{font-size:13px;fill:#334155}.value{font-size:13px;font-weight:700;fill:#0f172a}.bar{fill:#0ea5e9}</style>',
        '<text class="title" x="90" y="32">Revenue by region</text>',
    ]
    for tick in range(0, 5):
        value = max_value * tick / 4
        y = chart_top + chart_height - (value / max_value) * chart_height
        parts.append(f'<line class="grid" x1="{margin_left}" y1="{y:.1f}" x2="{margin_left + chart_width}" y2="{y:.1f}"/>')
        parts.append(f'<text class="label" x="{margin_left - 10}" y="{y + 4:.1f}" text-anchor="end">{value:.0f}</text>')
    parts.append(f'<line class="axis" x1="{margin_left}" y1="{chart_top}" x2="{margin_left}" y2="{chart_top + chart_height}"/>')
    parts.append(f'<line class="axis" x1="{margin_left}" y1="{chart_top + chart_height}" x2="{margin_left + chart_width}" y2="{chart_top + chart_height}"/>')
    for idx, item in enumerate(by_region):
        revenue = float(item["revenue"])
        region = str(item["region"])
        x = margin_left + idx * (bar_width + bar_gap)
        h = revenue / max_value * chart_height
        y = chart_top + chart_height - h
        parts.append(f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{h:.1f}" rx="8"/>')
        parts.append(f'<text class="value" x="{x + bar_width / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle">{revenue:.2f}</text>')
        parts.append(f'<text class="label" x="{x + bar_width / 2:.1f}" y="{chart_top + chart_height + 28}" text-anchor="middle">{escape(region)}</text>')
    parts.append(f'<text class="label" x="{margin_left + chart_width / 2}" y="{height - 18}" text-anchor="middle">Cleaned sales revenue after validation; unit: local currency</text>')
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def markdown_table(rows: list[dict[str, object]], key: str, value: str) -> str:
    lines = [f"| {key} | {value} |", "| --- | ---: |"]
    for row in rows:
        lines.append(f"| {row[key]} | {float(row[value]):.2f} |")
    return "\n".join(lines)


def write_report(path: Path, summary: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"""# Sales data processing report

## Headline

- Raw rows: {summary['raw_rows']}
- Clean rows: {summary['clean_rows']}
- Rejected rows: {summary['rejected_rows']}
- Total units: {summary['total_units']}
- Total revenue: {summary['total_revenue']:.2f}

## Revenue by region

{markdown_table(summary['by_region'], 'region', 'revenue')}

## Revenue by month

{markdown_table(summary['by_month'], 'month', 'revenue')}

## Revenue by product

{markdown_table(summary['by_product'], 'product', 'revenue')}

## Visible chart

Open `reports/region_revenue.svg` to see the generated bar chart.
"""
    path.write_text(text, encoding="utf-8")


def run_pipeline(root: Path) -> dict[str, object]:
    raw_path = root / "data" / "raw" / "sales.csv"
    clean_path = root / "data" / "processed" / "clean_sales.csv"
    reject_path = root / "data" / "processed" / "rejected_sales.csv"
    db_path = root / "data" / "processed" / "sales.sqlite3"
    summary_path = root / "reports" / "summary.json"
    svg_path = root / "reports" / "region_revenue.svg"
    report_path = root / "reports" / "report.md"

    generate_raw_csv(raw_path)
    clean_rows, rejects = clean_csv(raw_path, clean_path, reject_path)
    build_database(db_path, clean_rows)
    summary = build_summary(db_path, raw_count=len(RAW_ROWS), clean_count=len(clean_rows), reject_count=len(rejects))
    write_json(summary_path, summary)
    write_region_svg(svg_path, summary["by_region"])
    write_report(report_path, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the data processing and visualization pipeline.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="lab root directory")
    args = parser.parse_args()
    summary = run_pipeline(args.root)
    print(f"raw_rows={summary['raw_rows']}")
    print(f"clean_rows={summary['clean_rows']}")
    print(f"rejected_rows={summary['rejected_rows']}")
    print(f"total_units={summary['total_units']}")
    print(f"total_revenue={summary['total_revenue']:.2f}")
    top_region = summary["by_region"][0]
    top_product = summary["by_product"][0]
    print(f"top_region={top_region['region']}:{top_region['revenue']:.2f}")
    print(f"top_product={top_product['product']}:{top_product['revenue']:.2f}")
    print("pipeline_status=ok")


if __name__ == "__main__":
    main()
