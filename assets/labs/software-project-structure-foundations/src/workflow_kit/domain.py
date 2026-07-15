from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable

ALLOWED_STATUS = {"todo", "doing", "done"}


@dataclass(frozen=True)
class Task:
    task_id: int
    title: str
    status: str = "todo"
    owner: str = "unassigned"
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("task title must not be empty")
        if self.status not in ALLOWED_STATUS:
            raise ValueError(f"invalid status: {self.status}")
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, object]) -> "Task":
        return Task(
            task_id=int(data["task_id"]),
            title=str(data["title"]),
            status=str(data.get("status", "todo")),
            owner=str(data.get("owner", "unassigned")),
            created_at=str(data.get("created_at", "")),
        )


def next_task_id(tasks: Iterable[Task]) -> int:
    current = [task.task_id for task in tasks]
    return (max(current) + 1) if current else 1


def summarize(tasks: Iterable[Task]) -> dict[str, int]:
    summary = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for task in tasks:
        summary[task.status] += 1
    return summary
