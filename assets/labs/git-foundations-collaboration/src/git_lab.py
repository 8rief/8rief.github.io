#!/usr/bin/env python3
"""Run a local Git foundations and collaboration scenario."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    argv: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str


def run(argv: list[str], cwd: Path, *, check: bool = True) -> CommandResult:
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = CommandResult(
        argv=argv,
        cwd=str(cwd),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed: {argv}\nstdout={completed.stdout}\nstderr={completed.stderr}")
    return result


def git(repo: Path, args: list[str], *, check: bool = True) -> CommandResult:
    return run(["git", *args], repo, check=check)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(content)


def config_repo(repo: Path) -> None:
    git(repo, ["config", "user.name", "Git Lab Student"])
    git(repo, ["config", "user.email", "student@example.invalid"])
    git(repo, ["config", "core.filemode", "false"])


def rev(repo: Path, name: str) -> str:
    return git(repo, ["rev-parse", name]).stdout.strip()


def short(result: CommandResult, limit: int = 2000) -> dict[str, Any]:
    data = asdict(result)
    data["stdout"] = data["stdout"][:limit]
    data["stderr"] = data["stderr"][:limit]
    return data


def run_scenario(workspace: Path, outdir: Path) -> dict[str, Any]:
    if workspace.exists():
        shutil.rmtree(workspace)
    if outdir.exists():
        shutil.rmtree(outdir)
    workspace.mkdir(parents=True)
    outdir.mkdir(parents=True)

    observations: dict[str, Any] = {"commands": []}
    git_version = run(["git", "--version"], workspace)
    observations["git_version"] = git_version.stdout.strip()

    repo = workspace / "project"
    remote = workspace / "remote.git"
    colleague = workspace / "colleague"

    run(["git", "init", "-b", "main", str(repo)], workspace)
    config_repo(repo)
    write(repo / "README.md", "# local-report\n\nA small report project for learning Git.\n")
    write(repo / "src" / "report.txt", "title: Local Report\nstatus: draft\n")
    status_untracked = git(repo, ["status", "--short"])
    git(repo, ["add", "README.md", "src/report.txt"])
    status_staged = git(repo, ["status", "--short"])
    git(repo, ["commit", "-m", "Initial report skeleton"])
    first_commit = rev(repo, "HEAD")

    observations["working_tree_index_commit"] = {
        "status_untracked": short(status_untracked),
        "status_staged": short(status_staged),
        "first_commit": first_commit,
        "head_type": git(repo, ["cat-file", "-t", "HEAD"]).stdout.strip(),
        "tree_type": git(repo, ["cat-file", "-t", "HEAD^{tree}"]).stdout.strip(),
        "tree_entries": git(repo, ["ls-tree", "--name-only", "HEAD"]).stdout.splitlines(),
    }

    append(repo / "src" / "report.txt", "owner: team-a\n")
    unstaged_diff = git(repo, ["diff", "--", "src/report.txt"])
    git(repo, ["add", "src/report.txt"])
    staged_diff = git(repo, ["diff", "--staged", "--", "src/report.txt"])
    git(repo, ["commit", "-m", "Add report owner"])
    second_commit = rev(repo, "HEAD")
    observations["diff_and_patch"] = {
        "unstaged_diff_excerpt": unstaged_diff.stdout,
        "staged_diff_excerpt": staged_diff.stdout,
        "second_commit": second_commit,
    }

    git(repo, ["switch", "-c", "feature/summary"])
    append(repo / "README.md", "\n## Summary\n\nThe report has an owner and a status line.\n")
    git(repo, ["add", "README.md"])
    git(repo, ["commit", "-m", "Add summary section"])
    feature_commit = rev(repo, "HEAD")
    git(repo, ["switch", "main"])
    branch_refs_before_merge = git(repo, ["show-ref", "--heads"]).stdout.splitlines()
    git(repo, ["merge", "--no-ff", "feature/summary", "-m", "Merge summary section"])
    merge_commit = rev(repo, "HEAD")
    observations["branches_refs_head"] = {
        "feature_commit": feature_commit,
        "branch_refs_before_merge": branch_refs_before_merge,
        "merge_commit": merge_commit,
        "graph": git(repo, ["log", "--oneline", "--graph", "--decorate", "--all", "-n", "8"]).stdout,
    }

    # Reproduce a conflict on the same line and resolve it deliberately.
    git(repo, ["switch", "-c", "feature/status-ready"])
    report = repo / "src" / "report.txt"
    report.write_text(report.read_text(encoding="utf-8").replace("status: draft", "status: ready"), encoding="utf-8")
    git(repo, ["add", "src/report.txt"])
    git(repo, ["commit", "-m", "Mark report ready on feature"])
    git(repo, ["switch", "main"])
    report.write_text(report.read_text(encoding="utf-8").replace("status: draft", "status: review"), encoding="utf-8")
    git(repo, ["add", "src/report.txt"])
    git(repo, ["commit", "-m", "Mark report under review"])
    conflict_merge = git(repo, ["merge", "feature/status-ready"], check=False)
    conflict_file = report.read_text(encoding="utf-8")
    report.write_text(conflict_file.replace("<<<<<<< HEAD\nstatus: review\n=======\nstatus: ready\n>>>>>>> feature/status-ready", "status: ready\nreview: completed"), encoding="utf-8")
    git(repo, ["add", "src/report.txt"])
    git(repo, ["commit", "-m", "Resolve report status conflict"])
    conflict_resolved_commit = rev(repo, "HEAD")
    observations["merge_conflict"] = {
        "merge_returncode": conflict_merge.returncode,
        "merge_stderr_excerpt": conflict_merge.stderr,
        "conflict_markers_seen": all(marker in conflict_file for marker in ["<<<<<<<", "=======", ">>>>>>>"]),
        "resolved_file": report.read_text(encoding="utf-8"),
        "resolved_commit": conflict_resolved_commit,
    }

    # Demonstrate rebase on a local topic branch before sharing.
    git(repo, ["switch", "-c", "topic/reword-readme"])
    append(repo / "README.md", "\n## Local note\n\nThis branch will be rebased before sharing.\n")
    git(repo, ["add", "README.md"])
    git(repo, ["commit", "-m", "Add local note"])
    topic_before = rev(repo, "HEAD")
    git(repo, ["switch", "main"])
    append(repo / "docs" / "usage.md", "# Usage\n\nRun the report script after cloning.\n")
    git(repo, ["add", "docs/usage.md"])
    git(repo, ["commit", "-m", "Add usage note"])
    main_before_rebase = rev(repo, "HEAD")
    git(repo, ["switch", "topic/reword-readme"])
    git(repo, ["rebase", "main"])
    topic_after = rev(repo, "HEAD")
    git(repo, ["switch", "main"])
    git(repo, ["merge", "--ff-only", "topic/reword-readme"])
    observations["rebase_boundary"] = {
        "topic_before_rebase": topic_before,
        "main_before_rebase": main_before_rebase,
        "topic_after_rebase": topic_after,
        "hash_changed_by_rebase": topic_before != topic_after,
        "linear_graph": git(repo, ["log", "--oneline", "--graph", "--decorate", "-n", "8"]).stdout,
    }

    write(repo / ".gitignore", "build/\n*.tmp\n")
    write(repo / "build" / "ignored.tmp", "generated\n")
    write(repo / "notes.tmp", "temporary\n")
    ignored_status = git(repo, ["status", "--short", "--ignored"])
    git(repo, ["add", ".gitignore"])
    git(repo, ["commit", "-m", "Add ignore rules"])

    run(["git", "init", "--bare", str(remote)], workspace)
    git(repo, ["remote", "add", "origin", str(remote)])
    push_main = git(repo, ["push", "-u", "origin", "main"])
    git(repo, ["tag", "-a", "v0.1.0", "-m", "Local report lab release"])
    push_tag = git(repo, ["push", "origin", "v0.1.0"])
    run(["git", "clone", str(remote), str(colleague)], workspace)
    config_repo(colleague)
    append(colleague / "docs" / "usage.md", "\nColleague adds one review checklist line.\n")
    git(colleague, ["add", "docs/usage.md"])
    git(colleague, ["commit", "-m", "Add colleague checklist note"])
    colleague_push = git(colleague, ["push", "origin", "main"])
    fetch = git(repo, ["fetch", "origin"])
    local_before_pull = rev(repo, "main")
    remote_after_fetch = rev(repo, "origin/main")
    pull = git(repo, ["pull", "--ff-only"])
    local_after_pull = rev(repo, "main")
    observations["remote_collaboration"] = {
        "ignored_status": ignored_status.stdout.splitlines(),
        "push_main": short(push_main),
        "push_tag": short(push_tag),
        "colleague_push": short(colleague_push),
        "fetch": short(fetch),
        "local_before_pull": local_before_pull,
        "origin_main_after_fetch": remote_after_fetch,
        "local_after_pull": local_after_pull,
        "pull": short(pull),
        "tags": git(repo, ["tag", "--list", "--sort=creatordate"]).stdout.splitlines(),
        "final_graph": git(repo, ["log", "--oneline", "--graph", "--decorate", "--all", "-n", "12"]).stdout,
    }

    observations["final_status"] = git(repo, ["status", "--short"]).stdout.splitlines()
    observations["workspace_paths"] = {
        "project": str(repo),
        "remote": str(remote),
        "colleague": str(colleague),
    }
    (outdir / "observations.json").write_text(json.dumps(observations, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "git_foundations_report.md").write_text(render_report(observations), encoding="utf-8")
    return observations


def render_report(obs: dict[str, Any]) -> str:
    wt = obs["working_tree_index_commit"]
    diff = obs["diff_and_patch"]
    branch = obs["branches_refs_head"]
    conflict = obs["merge_conflict"]
    rebase = obs["rebase_boundary"]
    remote = obs["remote_collaboration"]
    report = f"""
# Git foundations and collaboration report

## Environment

- {obs['git_version']}

## Working tree, index, and commit

Untracked status:

```text
{wt['status_untracked']['stdout'].strip()}
```

Staged status:

```text
{wt['status_staged']['stdout'].strip()}
```

First commit: `{wt['first_commit']}`; `HEAD` type: `{wt['head_type']}`; root tree type: `{wt['tree_type']}`.

Root tree entries: `{', '.join(wt['tree_entries'])}`.

## Diff and patch boundary

Unstaged diff excerpt:

```diff
{diff['unstaged_diff_excerpt'].strip()}
```

Staged diff excerpt:

```diff
{diff['staged_diff_excerpt'].strip()}
```

## Branch, ref, and HEAD

Merge commit: `{branch['merge_commit']}`.

```text
{branch['graph'].strip()}
```

## Merge conflict

Merge return code: `{conflict['merge_returncode']}`; conflict markers seen: `{conflict['conflict_markers_seen']}`.

Resolved file:

```text
{conflict['resolved_file'].strip()}
```

## Rebase boundary

Topic before rebase: `{rebase['topic_before_rebase']}`.
Topic after rebase: `{rebase['topic_after_rebase']}`.
Hash changed by rebase: `{rebase['hash_changed_by_rebase']}`.

```text
{rebase['linear_graph'].strip()}
```

## Remote collaboration and release tag

Local before pull: `{remote['local_before_pull']}`.
Origin/main after fetch: `{remote['origin_main_after_fetch']}`.
Local after pull: `{remote['local_after_pull']}`.
Tags: `{', '.join(remote['tags'])}`.

```text
{remote['final_graph'].strip()}
```

## Final status

```text
{chr(10).join(obs['final_status']) if obs['final_status'] else 'clean except ignored files when shown explicitly'}
```
"""
    return textwrap.dedent(report).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    run_scenario(args.workspace, args.outdir)
    print(f"wrote {args.outdir / 'git_foundations_report.md'}")
    print(f"wrote {args.outdir / 'observations.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
