#!/usr/bin/env python3
"""Small application demonstrating validated config and structured logging."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence
import uuid


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "config" / "defaults.json"
CONFIG_KEYS = {"service_name", "host", "port", "log_level", "output_dir"}
ENV_KEYS = {
    "service_name": "DEMO_SERVICE_NAME",
    "host": "DEMO_HOST",
    "port": "DEMO_PORT",
    "log_level": "DEMO_LOG_LEVEL",
    "output_dir": "DEMO_OUTPUT_DIR",
}
LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
RUN_ID_RE = re.compile(r"[A-Za-z0-9._-]{1,64}\Z")


class ConfigError(ValueError):
    """Raised when a configuration layer violates the public schema."""


@dataclass(frozen=True)
class AppConfig:
    service_name: str
    host: str
    port: int
    log_level: str
    output_dir: str


@dataclass(frozen=True)
class ResolvedConfig:
    config: AppConfig
    sources: dict[str, str]
    secret_configured: bool


def load_json_object(path: Path, layer_name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"{layer_name} file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"{layer_name} is invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{layer_name} must contain one JSON object")
    unknown = sorted(set(value) - CONFIG_KEYS)
    if unknown:
        raise ConfigError(f"{layer_name} has unknown keys: {', '.join(unknown)}")
    return value


def validate_config(raw: Mapping[str, Any]) -> AppConfig:
    missing = sorted(CONFIG_KEYS - set(raw))
    if missing:
        raise ConfigError(f"missing required keys: {', '.join(missing)}")

    service_name = raw["service_name"]
    host = raw["host"]
    port = raw["port"]
    log_level = raw["log_level"]
    output_dir = raw["output_dir"]

    if not isinstance(service_name, str) or not service_name.strip():
        raise ConfigError("service_name must be a non-empty string")
    if not isinstance(host, str) or not host.strip():
        raise ConfigError("host must be a non-empty string")
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError("port must be an integer")
    if not 1 <= port <= 65535:
        raise ConfigError("port must be between 1 and 65535")
    if not isinstance(log_level, str) or log_level.upper() not in LOG_LEVELS:
        raise ConfigError("log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL")
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise ConfigError("output_dir must be a non-empty string")

    return AppConfig(
        service_name=service_name.strip(),
        host=host.strip(),
        port=port,
        log_level=log_level.upper(),
        output_dir=output_dir.strip(),
    )


def resolve_config(
    defaults_path: Path,
    config_path: Path | None,
    environ: Mapping[str, str],
    cli_values: Mapping[str, Any],
) -> ResolvedConfig:
    merged = load_json_object(defaults_path, "defaults")
    sources = {key: "defaults" for key in merged}

    if config_path is not None:
        file_values = load_json_object(config_path, "config")
        merged.update(file_values)
        sources.update({key: "file" for key in file_values})

    for key, env_name in ENV_KEYS.items():
        if env_name not in environ:
            continue
        raw: Any = environ[env_name]
        if key == "port":
            try:
                raw = int(raw)
            except ValueError:
                pass
        merged[key] = raw
        sources[key] = "env"

    for key in CONFIG_KEYS:
        value = cli_values.get(key)
        if value is not None:
            merged[key] = value
            sources[key] = "cli"

    return ResolvedConfig(
        config=validate_config(merged),
        sources=sources,
        secret_configured=bool(environ.get("DEMO_API_TOKEN")),
    )


class JsonLineFormatter(logging.Formatter):
    """Render one bounded JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", "message"),
            "run_id": getattr(record, "run_id", "unknown"),
            "message": record.getMessage(),
        }
        details = getattr(record, "details", None)
        if details is not None:
            payload["details"] = details
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def make_logger(level: str, events_file: Path) -> logging.Logger:
    events_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = JsonLineFormatter()
    logger = logging.getLogger("config_log_demo")
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(level)

    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(formatter)
    file_handler = logging.FileHandler(events_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(stream)
    logger.addHandler(file_handler)
    return logger


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Demonstrate validated config precedence and JSONL logging."
    )
    parser.add_argument("--defaults", type=Path, default=DEFAULTS_PATH)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--service-name")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--log-level")
    parser.add_argument("--output-dir")
    parser.add_argument("--events-file", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def run(argv: Sequence[str] | None = None, environ: Mapping[str, str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    env = os.environ if environ is None else environ
    run_id = args.run_id
    run_id = run_id or uuid.uuid4().hex
    if not RUN_ID_RE.fullmatch(run_id):
        parser.error("--run-id must contain 1-64 letters, digits, dot, underscore, or hyphen")

    cli_values = {
        "service_name": args.service_name,
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "output_dir": args.output_dir,
    }
    try:
        resolved = resolve_config(args.defaults, args.config, env, cli_values)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    config = resolved.config
    events_file = args.events_file or Path(config.output_dir) / "events.jsonl"
    logger = make_logger(config.log_level, events_file)
    extra = {"run_id": run_id}
    logger.debug(
        "configuration resolved",
        extra={**extra, "event": "config_resolved", "details": resolved.sources},
    )
    logger.info(
        "configuration validated",
        extra={**extra, "event": "config_validated"},
    )

    mode = "dry_run" if args.dry_run else "execute"
    logger.info(
        "execution plan selected",
        extra={**extra, "event": "execution_planned", "details": {"mode": mode}},
    )
    result: dict[str, Any] = {
        "status": "ok",
        "mode": mode,
        "run_id": run_id,
        "config": asdict(config),
        "sources": resolved.sources,
        "secret_configured": resolved.secret_configured,
    }
    if not args.dry_run:
        result_path = Path(config.output_dir) / "run_result.json"
        atomic_write_json(result_path, result)
        result["result_file"] = str(result_path)
    logger.info("run completed", extra={**extra, "event": "run_complete"})
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
