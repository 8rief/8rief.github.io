#!/usr/bin/env python3
"""Collect local OS/Linux file, process, environment, and pipeline observations."""
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


def run_command(argv: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> CommandResult:
    completed = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CommandResult(argv=argv, returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)


def prepare_workspace(workspace: Path) -> dict[str, Path]:
    workspace.mkdir(parents=True, exist_ok=True)
    files = workspace / "files"
    logs = workspace / "logs"
    generated = workspace / "generated"
    for directory in (files, logs, generated):
        directory.mkdir(parents=True, exist_ok=True)

    (files / "alpha.txt").write_text("alpha one\nalpha two\n", encoding="utf-8")
    (files / "beta.txt").write_text("beta one\nbeta two\nbeta three\n", encoding="utf-8")
    (logs / "events.log").write_text(
        "INFO checkout user=alice\n"
        "WARN retry user=bob\n"
        "INFO checkout user=alice\n"
        "ERROR timeout user=carol\n"
        "INFO login user=bob\n"
        "WARN retry user=bob\n",
        encoding="utf-8",
    )
    return {"files": files, "logs": logs, "generated": generated}


def file_record(path: Path) -> dict[str, Any]:
    st = path.stat()
    mode = st.st_mode
    return {
        "path": str(path),
        "name": path.name,
        "inode": st.st_ino,
        "file_type": "directory" if stat.S_ISDIR(mode) else "regular" if stat.S_ISREG(mode) else "other",
        "mode_octal": oct(stat.S_IMODE(mode)),
        "mode_symbolic": stat.filemode(mode),
        "size_bytes": st.st_size,
        "nlink": st.st_nlink,
        "uid": st.st_uid,
        "gid": st.st_gid,
    }


def filesystem_observations(paths: dict[str, Path]) -> list[dict[str, Any]]:
    targets = [paths["files"], paths["files"] / "alpha.txt", paths["files"] / "beta.txt", paths["logs"] / "events.log"]
    return [file_record(target) for target in targets]


def descriptor_demo(generated: Path) -> dict[str, Any]:
    target = generated / "fd-demo.txt"
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        duplicate = os.dup(fd)
        try:
            os.write(fd, b"written through original fd\n")
            os.write(duplicate, b"written through duplicated fd\n")
        finally:
            os.close(duplicate)
    finally:
        os.close(fd)
    return {
        "target": str(target),
        "content": target.read_text(encoding="utf-8").splitlines(),
        "explanation": "Both file descriptors point to the same open file description, so writes land in one file.",
    }


def process_observation() -> dict[str, Any]:
    current_pid = os.getpid()
    current_ppid = os.getppid()
    ps = run_command(["ps", "-o", "pid,ppid,stat,comm", "-p", str(current_pid)])
    proc_status = Path(f"/proc/{current_pid}/status")
    proc_lines: list[str] = []
    if proc_status.exists():
        for line in proc_status.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(("Name:", "State:", "Pid:", "PPid:", "Threads:")):
                proc_lines.append(line)
    return {
        "pid": current_pid,
        "ppid": current_ppid,
        "ps": asdict(ps),
        "proc_status_excerpt": proc_lines,
    }


def environment_observation() -> dict[str, Any]:
    env = os.environ.copy()
    env["OS_LAB_CHILD_MARKER"] = "visible-to-child"
    child = run_command(
        [sys.executable, "-c", "import os; print(os.environ.get('OS_LAB_CHILD_MARKER', 'missing'))"],
        env=env,
    )
    return {
        "parent_has_marker_before_spawn": "OS_LAB_CHILD_MARKER" in os.environ,
        "child_stdout": child.stdout.strip(),
        "child_returncode": child.returncode,
    }


def _create_umask_file(directory: Path) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "umask-demo.txt"
    previous_umask = os.umask(0o027)
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o666)
        try:
            os.write(fd, b"umask controls default permission bits\n")
        finally:
            os.close(fd)
    finally:
        os.umask(previous_umask)
    return file_record(target)


def permission_observation(generated: Path) -> dict[str, Any]:
    """Show umask on a POSIX filesystem and record WSL drvfs caveats when present."""
    workspace_record = _create_umask_file(generated / "permission-workspace")
    posix_dir = Path("/tmp") / f"os-linux-process-files-permissions-{os.getuid()}"
    posix_record = _create_umask_file(posix_dir)
    expected = "0o640"
    return {
        "requested_mode": "0o666",
        "umask": "0o027",
        "expected_regular_posix_mode": expected,
        "result_mode": posix_record["mode_octal"],
        "record": posix_record,
        "workspace_record": workspace_record,
        "workspace_permission_bits_effective": workspace_record["mode_octal"] == expected,
        "note": "The teaching observation uses /tmp because Windows-mounted WSL paths can report mount-derived permission bits.",
    }


def signal_observation() -> dict[str, Any]:
    script = "sleep 30 & pid=$!; kill -TERM \"$pid\"; wait \"$pid\"; printf 'wait_status=%s\\n' \"$?\""
    result = run_command(["bash", "-lc", script])
    return asdict(result)


def pipeline_observation(log_path: Path) -> dict[str, Any]:
    grep = run_command(["grep", "-E", "^(INFO|WARN|ERROR)", str(log_path)])
    counts = run_command(["bash", "-lc", f"grep -E '^(INFO|WARN|ERROR)' {str(log_path)!r} | awk '{{print $1}}' | sort | uniq -c"])
    users = run_command(["bash", "-lc", f"awk '{{print $3}}' {str(log_path)!r} | sort | uniq -c"])
    return {
        "source": str(log_path),
        "matched_lines": grep.stdout.splitlines(),
        "level_counts": counts.stdout.splitlines(),
        "user_counts": users.stdout.splitlines(),
        "commands": [asdict(grep), asdict(counts), asdict(users)],
    }


def collect(workspace: Path, outdir: Path) -> dict[str, Any]:
    paths = prepare_workspace(workspace)
    observations: dict[str, Any] = {
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "cwd": str(Path.cwd()),
        },
        "filesystem": filesystem_observations(paths),
        "file_descriptors": descriptor_demo(paths["generated"]),
        "process": process_observation(),
        "environment_variables": environment_observation(),
        "permissions": permission_observation(paths["generated"]),
        "signals": signal_observation(),
        "text_pipeline": pipeline_observation(paths["logs"] / "events.log"),
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "observations.json").write_text(json.dumps(observations, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "system_observer_report.md").write_text(render_markdown(observations), encoding="utf-8")
    return observations


def render_markdown(observations: dict[str, Any]) -> str:
    fs_lines = [
        f"- `{Path(item['path']).name}`: inode `{item['inode']}`, type `{item['file_type']}`, mode `{item['mode_symbolic']}`, size `{item['size_bytes']}` bytes"
        for item in observations["filesystem"]
    ]
    level_counts = "\n".join(observations["text_pipeline"]["level_counts"])
    user_counts = "\n".join(observations["text_pipeline"]["user_counts"])
    proc_excerpt = "\n".join(observations["process"]["proc_status_excerpt"])
    fd_lines = "\n".join(observations["file_descriptors"]["content"])
    permission = observations["permissions"]
    sections = [
        "# OS/Linux process and file observer report",
        "",
        "## Filesystem records",
        *fs_lines,
        "",
        "## File descriptor demo",
        f"Target: `{observations['file_descriptors']['target']}`",
        "",
        "```text",
        fd_lines,
        "```",
        "",
        "## Process snapshot",
        f"Current PID: `{observations['process']['pid']}`; parent PID: `{observations['process']['ppid']}`.",
        "",
        "```text",
        proc_excerpt,
        "```",
        "",
        "## Environment variable inheritance",
        f"Child saw marker: `{observations['environment_variables']['child_stdout']}`.",
        "",
        "## Permission demo",
        f"Requested mode `{permission['requested_mode']}` with umask `{permission['umask']}` produced `{permission['result_mode']}` on `{permission['record']['path']}`.",
        f"Workspace path mode was `{permission['workspace_record']['mode_octal']}`; POSIX bits effective there: `{permission['workspace_permission_bits_effective']}`.",
        "",
        "## Signal demo",
        "```text",
        observations["signals"]["stdout"].strip(),
        "```",
        "",
        "## Text pipeline counts",
        "Level counts:",
        "",
        "```text",
        level_counts,
        "```",
        "",
        "User counts:",
        "",
        "```text",
        user_counts,
        "```",
        "",
    ]
    return "\n".join(sections)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    collect(args.workspace, args.outdir)
    print(f"wrote {args.outdir / 'system_observer_report.md'}")
    print(f"wrote {args.outdir / 'observations.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
