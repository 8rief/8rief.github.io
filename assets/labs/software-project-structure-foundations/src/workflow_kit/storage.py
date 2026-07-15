from __future__ import annotations

import json
import os
from pathlib import Path
from .domain import Task

SCHEMA_VERSION = 1


def empty_state(project_name: str) -> dict[str, object]:
    return {"schema_version": SCHEMA_VERSION, "project": project_name, "tasks": []}


def load_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return empty_state("unnamed")
    data = json.loads(path.read_text(encoding="utf-8"))
    if int(data.get("schema_version", -1)) != SCHEMA_VERSION:
        raise ValueError("unsupported schema_version")
    if "tasks" not in data or not isinstance(data["tasks"], list):
        raise ValueError("state file must contain a tasks list")
    return data


def save_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def tasks_from_state(state: dict[str, object]) -> list[Task]:
    return [Task.from_dict(item) for item in state.get("tasks", [])]


def state_from_tasks(project_name: str, tasks: list[Task]) -> dict[str, object]:
    return {"schema_version": SCHEMA_VERSION, "project": project_name, "tasks": [task.to_dict() for task in tasks]}
