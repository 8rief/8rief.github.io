from __future__ import annotations

import argparse
from pathlib import Path
from .config import ProjectConfig
from .domain import Task, next_task_id, summarize
from .layout import create_layout, render_tree
from .storage import load_state, save_state, tasks_from_state, state_from_tasks


def data_path(root: Path) -> Path:
    return root / "data" / "tasks.json"


def cmd_init(args: argparse.Namespace) -> int:
    create_layout(ProjectConfig(root=args.root, name=args.name))
    print(f"initialized={args.root}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    state = load_state(data_path(args.root))
    tasks = tasks_from_state(state)
    task = Task(task_id=next_task_id(tasks), title=args.title, owner=args.owner, status=args.status)
    tasks.append(task)
    save_state(data_path(args.root), state_from_tasks(str(state.get("project", "unnamed")), tasks))
    print(f"added id={task.task_id} status={task.status} owner={task.owner} title={task.title}")
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    state = load_state(data_path(args.root))
    tasks = tasks_from_state(state)
    updated = []
    found = False
    for task in tasks:
        if task.task_id == args.task_id:
            updated.append(Task(task_id=task.task_id, title=task.title, owner=task.owner, status="done", created_at=task.created_at))
            found = True
        else:
            updated.append(task)
    if not found:
        raise SystemExit(f"missing task id: {args.task_id}")
    save_state(data_path(args.root), state_from_tasks(str(state.get("project", "unnamed")), updated))
    print(f"done id={args.task_id}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    tasks = tasks_from_state(load_state(data_path(args.root)))
    for task in tasks:
        print(f"{task.task_id}\t{task.status}\t{task.owner}\t{task.title}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    state = load_state(data_path(args.root))
    tasks = tasks_from_state(state)
    summary = summarize(tasks)
    report = args.root / "reports" / "summary.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Project summary", "", f"- project: {state.get('project', 'unnamed')}", f"- total: {len(tasks)}"]
    for status, count in summary.items():
        lines.append(f"- {status}: {count}")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report={report}")
    print(f"summary={summary}")
    return 0


def cmd_tree(args: argparse.Namespace) -> int:
    print(render_tree(args.root), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="workflow-kit")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--name", required=True)
    init.set_defaults(func=cmd_init)
    add = sub.add_parser("add")
    add.add_argument("--root", type=Path, required=True)
    add.add_argument("--owner", default="unassigned")
    add.add_argument("--status", default="todo", choices=["todo", "doing", "done"])
    add.add_argument("title")
    add.set_defaults(func=cmd_add)
    done = sub.add_parser("done")
    done.add_argument("--root", type=Path, required=True)
    done.add_argument("task_id", type=int)
    done.set_defaults(func=cmd_done)
    listing = sub.add_parser("list")
    listing.add_argument("--root", type=Path, required=True)
    listing.set_defaults(func=cmd_list)
    report = sub.add_parser("report")
    report.add_argument("--root", type=Path, required=True)
    report.set_defaults(func=cmd_report)
    tree = sub.add_parser("tree")
    tree.add_argument("--root", type=Path, required=True)
    tree.set_defaults(func=cmd_tree)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
