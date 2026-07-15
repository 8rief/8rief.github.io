#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Callable, Iterable
from xml.sax.saxutils import escape

SCHEMA_VERSION = 2

SEED_PRODUCTS = [
    ("NB-001", "Notebook", "stationery", 1299, 25),
    ("PN-010", "Pen set", "stationery", 499, 80),
    ("BK-200", "Backpack", "bags", 4599, 18),
    ("BT-404", "Bottle", "gear", 1899, 30),
]


@dataclass
class CacheEntry:
    value: object
    expires_at: float


class ManualClock:
    def __init__(self) -> None:
        self.now_value = 0.0

    def __call__(self) -> float:
        return self.now_value

    def advance(self, seconds: float) -> None:
        self.now_value += seconds


class TTLCache:
    def __init__(self, ttl_seconds: float, clock: Callable[[], float] | None = None) -> None:
        self.ttl_seconds = ttl_seconds
        self.clock = clock or monotonic
        self.entries: dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0
        self.invalidations = 0
        self.expirations = 0

    def get(self, key: str) -> object | None:
        entry = self.entries.get(key)
        if entry is None:
            self.misses += 1
            return None
        if entry.expires_at <= self.clock():
            self.expirations += 1
            self.misses += 1
            self.entries.pop(key, None)
            return None
        self.hits += 1
        return entry.value

    def set(self, key: str, value: object) -> None:
        self.entries[key] = CacheEntry(value=value, expires_at=self.clock() + self.ttl_seconds)

    def invalidate(self, key: str) -> None:
        if key in self.entries:
            self.invalidations += 1
            self.entries.pop(key, None)

    def stats(self) -> dict[str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "invalidations": self.invalidations,
            "expirations": self.expirations,
        }


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def user_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    applied: list[str] = []
    version = user_version(conn)
    if version < 1:
        conn.executescript(
            """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK(price_cents > 0),
                stock INTEGER NOT NULL CHECK(stock >= 0),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                customer TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE order_items (
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents > 0),
                PRIMARY KEY(order_id, product_id)
            );
            PRAGMA user_version = 1;
            """
        )
        applied.append("001_initial_schema")
        version = 1
    if version < 2:
        conn.executescript(
            """
            CREATE INDEX idx_products_category ON products(category, sku);
            CREATE INDEX idx_order_items_product_id ON order_items(product_id);
            PRAGMA user_version = 2;
            """
        )
        applied.append("002_indexes")
    conn.commit()
    return applied


def seed_products(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """
        INSERT INTO products(sku, name, category, price_cents, stock)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(sku) DO UPDATE SET
            name=excluded.name,
            category=excluded.category,
            price_cents=excluded.price_cents,
            stock=excluded.stock,
            updated_at=CURRENT_TIMESTAMP
        """,
        SEED_PRODUCTS,
    )
    conn.commit()


def create_product(conn: sqlite3.Connection, sku: str, name: str, category: str, price_cents: int, stock: int) -> int:
    cur = conn.execute(
        "INSERT INTO products(sku, name, category, price_cents, stock) VALUES (?, ?, ?, ?, ?)",
        (sku, name, category, price_cents, stock),
    )
    conn.commit()
    return int(cur.lastrowid)


def update_stock(conn: sqlite3.Connection, sku: str, delta: int) -> None:
    cur = conn.execute(
        "UPDATE products SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP WHERE sku = ? AND stock + ? >= 0",
        (delta, sku, delta),
    )
    if cur.rowcount != 1:
        raise ValueError(f"stock update failed for {sku}")
    conn.commit()


def find_products_by_category(conn: sqlite3.Connection, category: str) -> list[dict[str, object]]:
    rows = conn.execute(
        "SELECT sku, name, category, price_cents, stock FROM products WHERE category = ? ORDER BY sku",
        (category,),
    ).fetchall()
    return [dict(row) for row in rows]


def explain_category_query(conn: sqlite3.Connection, category: str) -> list[str]:
    rows = conn.execute(
        "EXPLAIN QUERY PLAN SELECT sku, name FROM products WHERE category = ? ORDER BY sku",
        (category,),
    ).fetchall()
    return [str(row[3]) for row in rows]


def place_order(conn: sqlite3.Connection, customer: str, items: Iterable[tuple[str, int]]) -> int:
    normalized = [(sku, int(quantity)) for sku, quantity in items]
    if not normalized:
        raise ValueError("order must contain at least one item")
    try:
        with conn:
            order_id = conn.execute("INSERT INTO orders(customer) VALUES (?)", (customer,)).lastrowid
            for sku, quantity in normalized:
                row = conn.execute(
                    "SELECT id, price_cents, stock FROM products WHERE sku = ?",
                    (sku,),
                ).fetchone()
                if row is None:
                    raise ValueError(f"unknown sku {sku}")
                if row["stock"] < quantity:
                    raise ValueError(f"insufficient stock for {sku}")
                conn.execute(
                    "UPDATE products SET stock = stock - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (quantity, row["id"]),
                )
                conn.execute(
                    "INSERT INTO order_items(order_id, product_id, quantity, unit_price_cents) VALUES (?, ?, ?, ?)",
                    (order_id, row["id"], quantity, row["price_cents"]),
                )
    except sqlite3.Error as exc:
        raise RuntimeError("database transaction failed") from exc
    return int(order_id)


def category_report_from_db(conn: sqlite3.Connection) -> list[dict[str, object]]:
    rows = conn.execute(
        """
        WITH sold AS (
            SELECT product_id,
                   SUM(quantity) AS units_sold,
                   SUM(quantity * unit_price_cents) AS revenue_cents
            FROM order_items
            GROUP BY product_id
        )
        SELECT p.category AS category,
               SUM(p.stock) AS stock_left,
               COALESCE(SUM(sold.units_sold), 0) AS units_sold,
               COALESCE(SUM(sold.revenue_cents), 0) AS revenue_cents
        FROM products p
        LEFT JOIN sold ON sold.product_id = p.id
        GROUP BY p.category
        ORDER BY revenue_cents DESC, category
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_category_report(conn: sqlite3.Connection, cache: TTLCache) -> list[dict[str, object]]:
    cached = cache.get("category_report")
    if cached is not None:
        return cached  # type: ignore[return-value]
    report = category_report_from_db(conn)
    cache.set("category_report", report)
    return report


def database_summary(conn: sqlite3.Connection) -> dict[str, object]:
    product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    order_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_revenue_cents = conn.execute(
        "SELECT COALESCE(SUM(quantity * unit_price_cents), 0) FROM order_items"
    ).fetchone()[0]
    total_stock = conn.execute("SELECT SUM(stock) FROM products").fetchone()[0]
    return {
        "schema_version": user_version(conn),
        "product_count": int(product_count),
        "order_count": int(order_count),
        "total_revenue_cents": int(total_revenue_cents),
        "total_stock": int(total_stock),
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_svg(path: Path, category_report: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 760, 420
    left, top, chart_w, chart_h = 92, 58, 590, 260
    max_value = max(int(row["revenue_cents"]) for row in category_report) or 1
    bar_gap = 28
    bar_w = (chart_w - bar_gap * (len(category_report) - 1)) / len(category_report)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Revenue by category</title>',
        '<desc id="desc">Revenue by category after transaction-backed orders and cache-aside report refresh.</desc>',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif}.title{font-size:22px;font-weight:700;fill:#0f172a}.axis{stroke:#475569;stroke-width:1.5}.grid{stroke:#e2e8f0}.label{font-size:13px;fill:#334155}.value{font-size:13px;font-weight:700;fill:#0f172a}.bar{fill:#f97316}</style>',
        '<text class="title" x="92" y="34">Revenue by category</text>',
    ]
    for tick in range(5):
        value = max_value * tick / 4
        y = top + chart_h - (value / max_value) * chart_h
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}"/>')
        parts.append(f'<text class="label" x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{value/100:.0f}</text>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}"/>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}"/>')
    for idx, row in enumerate(category_report):
        revenue = int(row["revenue_cents"])
        category = str(row["category"])
        x = left + idx * (bar_w + bar_gap)
        h = revenue / max_value * chart_h
        y = top + chart_h - h
        parts.append(f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="8"/>')
        parts.append(f'<text class="value" x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle">{revenue/100:.2f}</text>')
        parts.append(f'<text class="label" x="{x + bar_w / 2:.1f}" y="{top + chart_h + 28}" text-anchor="middle">{escape(category)}</text>')
    parts.append(f'<text class="label" x="{left + chart_w / 2}" y="{height - 18}" text-anchor="middle">Unit: currency; source: SQLite category report</text>')
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def write_markdown(path: Path, summary: dict[str, object], category_report: list[dict[str, object]], cache_stats: dict[str, int], plan: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Database and cache practice report",
        "",
        "## Headline",
        "",
        f"- Schema version: {summary['schema_version']}",
        f"- Products: {summary['product_count']}",
        f"- Orders: {summary['order_count']}",
        f"- Total revenue: {summary['total_revenue_cents'] / 100:.2f}",
        f"- Total stock left: {summary['total_stock']}",
        "",
        "## Category report",
        "",
        "| category | stock left | units sold | revenue |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in category_report:
        lines.append(f"| {row['category']} | {row['stock_left']} | {row['units_sold']} | {int(row['revenue_cents']) / 100:.2f} |")
    lines.extend([
        "",
        "## Cache stats",
        "",
        f"- Hits: {cache_stats['hits']}",
        f"- Misses: {cache_stats['misses']}",
        f"- Invalidations: {cache_stats['invalidations']}",
        f"- Expirations: {cache_stats['expirations']}",
        "",
        "## Query plan",
        "",
    ])
    lines.extend(f"- {item}" for item in plan)
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_demo(root: Path) -> dict[str, object]:
    db_path = root / "data" / "app.sqlite3"
    if db_path.exists():
        db_path.unlink()
    with connect(db_path) as conn:
        migrations = apply_migrations(conn)
        seed_products(conn)
        create_product(conn, "MG-777", "Mug", "gear", 1599, 12)
        update_stock(conn, "MG-777", 3)
        gear = find_products_by_category(conn, "gear")
        query_plan = explain_category_query(conn, "gear")
        clock = ManualClock()
        cache = TTLCache(ttl_seconds=5, clock=clock)
        initial_report = get_category_report(conn, cache)
        cached_report = get_category_report(conn, cache)
        assert initial_report == cached_report
        order_one = place_order(conn, "alice", [("BK-200", 2), ("PN-010", 3)])
        cache.invalidate("category_report")
        order_two = place_order(conn, "bob", [("NB-001", 4), ("BT-404", 1)])
        refreshed_report = get_category_report(conn, cache)
        clock.advance(6)
        expired_report = get_category_report(conn, cache)
        assert refreshed_report == expired_report
        summary = database_summary(conn)
        payload = {
            "migrations": migrations,
            "created_product_sku": "MG-777",
            "gear_product_count": len(gear),
            "order_ids": [order_one, order_two],
            "summary": summary,
            "category_report": expired_report,
            "cache_stats": cache.stats(),
            "category_query_plan": query_plan,
            "query_plan_uses_index": any("idx_products_category" in item for item in query_plan),
        }
        write_json(root / "reports" / "summary.json", payload)
        write_svg(root / "reports" / "category_revenue.svg", expired_report)
        write_markdown(root / "reports" / "report.md", summary, expired_report, cache.stats(), query_plan)
        return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the database and cache practice demo.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    payload = run_demo(args.root)
    summary = payload["summary"]
    cache = payload["cache_stats"]
    print(f"schema_version={summary['schema_version']}")
    print(f"product_count={summary['product_count']}")
    print(f"order_count={summary['order_count']}")
    print(f"total_revenue_cents={summary['total_revenue_cents']}")
    print(f"total_stock={summary['total_stock']}")
    print(f"cache_hits={cache['hits']}")
    print(f"cache_misses={cache['misses']}")
    print(f"cache_invalidations={cache['invalidations']}")
    print(f"cache_expirations={cache['expirations']}")
    print(f"query_plan_uses_index={payload['query_plan_uses_index']}")
    print("database_cache_status=ok")


if __name__ == "__main__":
    main()
