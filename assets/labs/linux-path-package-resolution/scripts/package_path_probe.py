#!/usr/bin/env python3
"""Probe how Linux resolves commands through PATH, shell builtins, and dpkg metadata."""

from __future__ import annotations

import json
import os
import shutil
import shlex
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNTIME = Path("/tmp/path-lab")
BIN_FIRST = RUNTIME / "first"
BIN_SECOND = RUNTIME / "second"
BIN_NOEXEC = RUNTIME / "not_executable"


@dataclass
class ProbeResult:
    name: str
    argv: list[str]
    returncode: int
    ok: bool
    expected_tokens: list[str]
    missing_tokens: list[str]
    first_lines: list[str]
    note: str


def write_demo_tools() -> None:
    if RUNTIME.exists():
        shutil.rmtree(RUNTIME)
    for directory in (BIN_FIRST, BIN_SECOND, BIN_NOEXEC):
        directory.mkdir(parents=True, exist_ok=True)
    first = BIN_FIRST / "demo-tool"
    second = BIN_SECOND / "demo-tool"
    noexec = BIN_NOEXEC / "demo-tool"
    first.write_text("#!/usr/bin/env bash\necho first-bin\n", encoding="utf-8")
    second.write_text("#!/usr/bin/env bash\necho second-bin\n", encoding="utf-8")
    noexec.write_text("#!/usr/bin/env bash\necho noexec-bin\n", encoding="utf-8")
    first.chmod(0o755)
    second.chmod(0o755)
    noexec.chmod(0o644)


def run(
    name: str,
    argv: Sequence[str],
    expected: Sequence[str],
    note: str,
    env: Mapping[str, str] | None = None,
    timeout: float = 8.0,
) -> ProbeResult:
    completed = subprocess.run(
        list(argv),
        cwd=ROOT,
        env=dict(env) if env is not None else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    output = completed.stdout.replace("\r\n", "\n")
    missing = [token for token in expected if token not in output]
    return ProbeResult(
        name=name,
        argv=list(argv),
        returncode=completed.returncode,
        ok=completed.returncode == 0 and not missing,
        expected_tokens=list(expected),
        missing_tokens=missing,
        first_lines=output.splitlines()[:10],
        note=note,
    )


def shell_env(path_value: str) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = path_value
    return env


def build_probes() -> list[ProbeResult]:
    write_demo_tools()
    default_path = os.environ.get("PATH", "")
    first_path = f"{BIN_FIRST}:{BIN_SECOND}:{default_path}"
    second_path = f"{BIN_SECOND}:{BIN_FIRST}:{default_path}"
    noexec_path = f"{BIN_NOEXEC}:{BIN_FIRST}:{default_path}"
    results: list[ProbeResult] = []
    results.append(
        run(
            "current-path",
            ["bash", "-lc", "printf '%s\\n' \"$PATH\" | tr ':' '\\n' | sed -n '1,5p'"],
            [str(BIN_FIRST), str(BIN_SECOND), "/usr/bin"],
            "PATH is an ordered list of directories. The shell searches them from left to right.",
            env=shell_env(f"{BIN_FIRST}:{BIN_SECOND}:/usr/bin:/bin"),
        )
    )
    results.append(
        run(
            "external-command-location",
            ["bash", "-lc", "command -v python3 && python3 --version"],
            ["/usr/bin/python3", "Python"],
            "`command -v` records the executable path that the current shell will use for a command name.",
        )
    )
    results.append(
        run(
            "builtin-versus-external",
            ["bash", "-lc", "type -a printf | sed -n '1,4p'"],
            ["printf is a shell builtin", "printf is /usr/bin/printf"],
            "`type -a` exposes shell builtins and every external command candidate, which `which` often hides.",
        )
    )
    results.append(
        run(
            "path-order-first",
            ["bash", "-lc", "command -v demo-tool && demo-tool"],
            [str(BIN_FIRST / "demo-tool"), "first-bin"],
            "When two PATH directories contain the same executable name, the leftmost executable wins.",
            env=shell_env(first_path),
        )
    )
    results.append(
        run(
            "path-order-second",
            ["bash", "-lc", "command -v demo-tool && demo-tool"],
            [str(BIN_SECOND / "demo-tool"), "second-bin"],
            "Swapping the PATH order changes the selected executable without changing the command name.",
            env=shell_env(second_path),
        )
    )
    results.append(
        run(
            "execute-bit-boundary",
            ["bash", "-lc", "command -v demo-tool && demo-tool"],
            [str(BIN_FIRST / "demo-tool"), "first-bin"],
            "A file in a PATH directory still needs execute permission; a non-executable file is skipped for command lookup.",
            env=shell_env(noexec_path),
        )
    )
    results.append(
        run(
            "package-owner",
            ["bash", "-lc", "dpkg-query -S /usr/bin/python3 | sed -n '1p'"],
            ["python3-minimal", "/usr/bin/python3"],
            "On Debian/Ubuntu systems, dpkg metadata can tell which installed package owns a file.",
        )
    )
    results.append(
        run(
            "package-file-list",
            ["bash", "-lc", "dpkg-query -L coreutils | grep -E '/usr/bin/(ls|printf)$' | sort"],
            ["/usr/bin/ls", "/usr/bin/printf"],
            "Listing package files connects a command path back to the package that installed it.",
        )
    )
    results.append(
        run(
            "package-version-policy",
            ["bash", "-lc", "apt-cache policy coreutils | sed -n '1,6p'"],
            ["Installed:", "Candidate:"],
            "`apt-cache policy` records the installed and candidate package versions without installing anything.",
        )
    )
    return results


def write_transcript(results: list[ProbeResult]) -> None:
    lines = ["# PATH and package resolution transcript", ""]
    for result in results:
        cmd = " ".join(shlex.quote(part) for part in result.argv)
        lines.extend(
            [
                f"## {result.name}",
                "",
                f"command: `{cmd}`",
                f"returncode: `{result.returncode}`",
                f"check: `{'PASS' if result.ok else 'FAIL'}`",
                "",
                "first output lines:",
                "```text",
                *(result.first_lines or ["<no output>"]),
                "```",
                "",
                result.note,
                "",
            ]
        )
    (REPORTS / "transcript.md").write_text("\n".join(lines), encoding="utf-8")


def write_summary(results: list[ProbeResult]) -> None:
    lines = [
        "# Resolution summary",
        "",
        "| Probe | What changed or was inspected | Result |",
        "| --- | --- | --- |",
    ]
    for result in results:
        lines.append(f"| {result.name} | {result.note} | {'PASS' if result.ok else 'FAIL'} |")
    lines.extend(
        [
            "",
            "A reproducible debugging note for command lookup should record:",
            "",
            "1. the command name and the exact path selected by the shell;",
            "2. whether the name is a shell builtin, alias, function, or external executable;",
            "3. the PATH value or controlled PATH prefix used by the test;",
            "4. the package owner and installed version when the file comes from the OS package manager.",
        ]
    )
    (REPORTS / "resolution_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    results = build_probes()
    (REPORTS / "package_path_probe.json").write_text(
        json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_transcript(results)
    write_summary(results)
    failed = [result.name for result in results if not result.ok]
    print(json.dumps({"probes": len(results), "failed": failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
