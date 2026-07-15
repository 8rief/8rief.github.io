#!/usr/bin/env python3
"""Build a deterministic summary and publish files with atomic replacement."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping, Sequence


CONFIG_KEYS = {"currency", "include_statuses"}
ORDER_KEYS = {"order_id", "status", "amount_cents"}
CONTROLLED_FAILURE_RC = 70


class PipelineError(ValueError):
    """Raised when an input or config violates the pipeline contract."""


class ForcedBeforeReplace(RuntimeError):
    """Raised by the lab to prove the old artifact remains published."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def load_config(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise PipelineError(f"config file not found: {path}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PipelineError(
            f"config is invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, dict):
        raise PipelineError("config must contain one JSON object")
    unknown = sorted(set(value) - CONFIG_KEYS)
    missing = sorted(CONFIG_KEYS - set(value))
    if unknown:
        raise PipelineError(f"config has unknown keys: {', '.join(unknown)}")
    if missing:
        raise PipelineError(f"config is missing keys: {', '.join(missing)}")
    currency = value["currency"]
    statuses = value["include_statuses"]
    if not isinstance(currency, str) or not currency.strip():
        raise PipelineError("currency must be a non-empty string")
    if (
        not isinstance(statuses, list)
        or not statuses
        or any(not isinstance(item, str) or not item for item in statuses)
    ):
        raise PipelineError("include_statuses must be a non-empty list of strings")
    if len(set(statuses)) != len(statuses):
        raise PipelineError("include_statuses must not contain duplicates")
    return {"currency": currency, "include_statuses": statuses}, raw


def load_orders(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise PipelineError(f"input file not found: {path}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PipelineError("input must be valid UTF-8") from exc
    orders: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PipelineError(f"input line {line_number} is invalid JSON") from exc
        if not isinstance(value, dict) or set(value) != ORDER_KEYS:
            raise PipelineError(
                f"input line {line_number} must have exactly: {', '.join(sorted(ORDER_KEYS))}"
            )
        order_id = value["order_id"]
        status = value["status"]
        amount = value["amount_cents"]
        if not isinstance(order_id, str) or not order_id:
            raise PipelineError(f"input line {line_number} has invalid order_id")
        if order_id in seen_ids:
            raise PipelineError(f"duplicate order_id: {order_id}")
        if not isinstance(status, str) or not status:
            raise PipelineError(f"input line {line_number} has invalid status")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise PipelineError(f"input line {line_number} has invalid amount_cents")
        seen_ids.add(order_id)
        orders.append(value)
    if not orders:
        raise PipelineError("input must contain at least one order")
    return orders, raw


def build_summary(orders: list[dict[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]:
    included = set(config["include_statuses"])
    selected = [order for order in orders if order["status"] in included]
    counts = Counter(order["status"] for order in selected)
    return {
        "schema_version": 1,
        "currency": config["currency"],
        "included_statuses": sorted(included),
        "selected_order_count": len(selected),
        "total_amount_cents": sum(order["amount_cents"] for order in selected),
        "count_by_status": {key: counts[key] for key in sorted(counts)},
    }


def fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write(path: Path, data: bytes, fail_before_replace: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if fail_before_replace:
            raise ForcedBeforeReplace("forced failure before os.replace")
        os.replace(temporary_path, path)
        temporary_path = None
        fsync_directory(path.parent)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def run_pipeline(
    input_path: Path,
    config_path: Path,
    output_path: Path,
    manifest_path: Path,
    fail_before_replace: bool = False,
) -> dict[str, Any]:
    orders, input_bytes = load_orders(input_path)
    config, config_bytes = load_config(config_path)
    summary = build_summary(orders, config)
    output_bytes = canonical_json_bytes(summary)
    atomic_write(output_path, output_bytes, fail_before_replace=fail_before_replace)

    manifest = {
        "schema_version": 1,
        "input_sha256": sha256_bytes(input_bytes),
        "config_sha256": sha256_bytes(config_bytes),
        "output_sha256": sha256_bytes(output_bytes),
        "output_bytes": len(output_bytes),
        "selected_order_count": summary["selected_order_count"],
    }
    atomic_write(manifest_path, canonical_json_bytes(manifest))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and atomically publish a deterministic order summary."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--fail-before-replace", action="store_true")
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = run_pipeline(
            args.input,
            args.config,
            args.output,
            args.manifest,
            fail_before_replace=args.fail_before_replace,
        )
    except ForcedBeforeReplace as exc:
        print(f"pipeline forced failure: {exc}", file=sys.stderr)
        return CONTROLLED_FAILURE_RC
    except PipelineError as exc:
        print(f"pipeline input error: {exc}", file=sys.stderr)
        return 2
    print(
        "pipeline_ok "
        f"selected={manifest['selected_order_count']} "
        f"output_sha256={manifest['output_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
