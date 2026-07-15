from __future__ import annotations

from pathlib import Path
from .config import ProjectConfig, project_paths
from .storage import empty_state, save_state

README_TEMPLATE = """# {name}\n\nA small project skeleton created by the software project structure lab.\n\n## Commands\n\n- Add work item: `workflow-kit add --root . \"write README\"`\n- List work items: `workflow-kit list --root .`\n- Generate report: `workflow-kit report --root .`\n"""


def create_layout(config: ProjectConfig) -> None:
    config.validate()
    root = config.root
    root.mkdir(parents=True, exist_ok=True)
    for folder in project_paths(root).values():
        folder.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text(README_TEMPLATE.format(name=config.name), encoding="utf-8")
    (root / ".gitignore").write_text(".lab_tmp/\n__pycache__/\n*.pyc\n.env\nreports/*.tmp\n", encoding="utf-8")
    (root / "docs" / "architecture.md").write_text("# Architecture\n\nCore domain logic stays separate from CLI and storage adapters.\n", encoding="utf-8")
    (root / "config" / "example.json").write_text('{"log_level":"info","data_file":"data/tasks.json"}\n', encoding="utf-8")
    save_state(root / "data" / "tasks.json", empty_state(config.name))


def render_tree(root: Path) -> str:
    lines = [root.name + "/"]
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root)
        lines.append("  " + str(rel))
    return "\n".join(lines) + "\n"
