#!/usr/bin/env python3
"""Probe environment inheritance, bash startup hooks, and project env isolation."""

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
RUNTIME = Path("/tmp/env-profile-lab")
HOME_DIR = RUNTIME / "home"
PROJECT = RUNTIME / "project"
PROJECT_BIN = PROJECT / "bin"


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


def prepare_runtime() -> None:
    if RUNTIME.exists():
        shutil.rmtree(RUNTIME)
    (HOME_DIR / "login-bin").mkdir(parents=True, exist_ok=True)
    (HOME_DIR / "interactive-bin").mkdir(parents=True, exist_ok=True)
    PROJECT_BIN.mkdir(parents=True, exist_ok=True)
    (HOME_DIR / ".bash_profile").write_text(
        "export LOGIN_MARKER=from_bash_profile\n"
        "export PATH=\"$HOME/login-bin:$PATH\"\n",
        encoding="utf-8",
    )
    (HOME_DIR / ".bashrc").write_text(
        "export INTERACTIVE_MARKER=from_bashrc\n"
        "export PATH=\"$HOME/interactive-bin:$PATH\"\n",
        encoding="utf-8",
    )
    (PROJECT / "bash_env.sh").write_text(
        "export NONINTERACTIVE_MARKER=from_BASH_ENV\n",
        encoding="utf-8",
    )
    (PROJECT / "env.sh").write_text(
        f"export PROJECT_ROOT={shlex.quote(str(PROJECT))}\n"
        "export DEMO_APP_ENV=development\n"
        "export DEMO_CONFIG=config/dev.toml\n"
        "export PATH=\"$PROJECT_ROOT/bin:$PATH\"\n",
        encoding="utf-8",
    )
    (PROJECT / ".env.example").write_text(
        "DEMO_APP_ENV=development\nDEMO_CONFIG=config/dev.toml\n",
        encoding="utf-8",
    )
    tool = PROJECT_BIN / "demo-env-tool"
    tool.write_text("#!/usr/bin/env bash\necho demo-env-tool from project-bin\n", encoding="utf-8")
    tool.chmod(0o755)


def base_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(HOME_DIR)
    env["PATH"] = "/usr/bin:/bin"
    if extra:
        env.update(extra)
    return env


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
        first_lines=output.splitlines()[:12],
        note=note,
    )


def build_probes() -> list[ProbeResult]:
    prepare_runtime()
    results: list[ProbeResult] = []
    results.append(
        run(
            "local-variable-not-inherited",
            ["bash", "--noprofile", "--norc", "-c", "LOCAL_ONLY=hidden; python3 -c 'import os; print(os.getenv(\"LOCAL_ONLY\", \"unset\"))'"],
            ["unset"],
            "A plain shell variable is not part of the child process environment until it is exported.",
            env=base_env(),
        )
    )
    results.append(
        run(
            "exported-variable-inherited",
            ["bash", "--noprofile", "--norc", "-c", "export EXPORTED_VALUE=visible; python3 -c 'import os; print(os.getenv(\"EXPORTED_VALUE\", \"unset\"))'"],
            ["visible"],
            "`export` moves the name/value pair into the environment inherited by child processes.",
            env=base_env(),
        )
    )
    results.append(
        run(
            "minimal-env-boundary",
            ["env", "-i", "HOME=/tmp/env-profile-lab/home", "PATH=/usr/bin:/bin", "bash", "--noprofile", "--norc", "-c", "printf 'HOME=%s\\nPATH=%s\\nDEMO=%s\\n' \"$HOME\" \"$PATH\" \"${DEMO_APP_ENV:-unset}\"; command -v python3"],
            ["HOME=/tmp/env-profile-lab/home", "PATH=/usr/bin:/bin", "DEMO=unset", "/usr/bin/python3"],
            "`env -i` starts from a nearly empty environment, then adds back only the variables needed for the command.",
        )
    )
    results.append(
        run(
            "interactive-bashrc",
            [
                "bash",
                "--noprofile",
                "--norc",
                "-c",
                f"bash --rcfile {shlex.quote(str(HOME_DIR / '.bashrc'))} -i -c "
                "'printf '\\''INTERACTIVE_MARKER=%s\\n'\\'' \"${INTERACTIVE_MARKER:-unset}\"; "
                "printf '\\''PATH_HEAD=%s\\n'\\'' \"${PATH%%:*}\"' 2>/dev/null "
                "| grep -E '^(INTERACTIVE_MARKER|PATH_HEAD)='",
            ],
            ["INTERACTIVE_MARKER=from_bashrc", f"PATH_HEAD={HOME_DIR}/interactive-bin"],
            "An interactive Bash shell reads its rc file; this is where prompt and interactive aliases usually belong.",
            env=base_env(),
        )
    )
    results.append(
        run(
            "profile-source-boundary",
            ["bash", "--noprofile", "--norc", "-c", f"source {shlex.quote(str(HOME_DIR / '.bash_profile'))}; printf 'LOGIN_MARKER=%s\\n' \"${{LOGIN_MARKER:-unset}}\"; printf 'PATH_HEAD=%s\\n' \"${{PATH%%:*}}\""],
            ["LOGIN_MARKER=from_bash_profile", f"PATH_HEAD={HOME_DIR}/login-bin"],
            "A profile file is just shell code; sourcing it mutates the current shell environment.",
            env=base_env(),
        )
    )
    results.append(
        run(
            "bash-env-noninteractive",
            ["bash", "--noprofile", "--norc", "-c", "printf 'NONINTERACTIVE_MARKER=%s\\n' \"${NONINTERACTIVE_MARKER:-unset}\""],
            ["NONINTERACTIVE_MARKER=from_BASH_ENV"],
            "For non-interactive Bash, `BASH_ENV` points to a file that Bash reads before running the command.",
            env=base_env({"BASH_ENV": str(PROJECT / "bash_env.sh")}),
        )
    )
    results.append(
        run(
            "project-env-source",
            ["bash", "--noprofile", "--norc", "-c", f"source {shlex.quote(str(PROJECT / 'env.sh'))}; command -v demo-env-tool; demo-env-tool; python3 -c 'import os; print(os.getenv(\"DEMO_APP_ENV\")); print(os.getenv(\"DEMO_CONFIG\"))'"],
            [f"{PROJECT_BIN}/demo-env-tool", "demo-env-tool from project-bin", "development", "config/dev.toml"],
            "A project env script can add project-local tools to PATH and export non-secret configuration for child processes.",
            env=base_env(),
        )
    )
    results.append(
        run(
            "subshell-does-not-leak-upward",
            ["bash", "--noprofile", "--norc", "-c", f"( source {shlex.quote(str(PROJECT / 'env.sh'))}; printf 'inside=%s\\n' \"$DEMO_APP_ENV\" ); printf 'outside=%s\\n' \"${{DEMO_APP_ENV:-unset}}\""],
            ["inside=development", "outside=unset"],
            "A subshell inherits from the parent and can mutate its own environment, but those mutations do not leak back upward.",
            env=base_env(),
        )
    )
    return results


def write_transcript(results: list[ProbeResult]) -> None:
    lines = ["# Environment/profile/project isolation transcript", ""]
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
        "# Environment isolation summary",
        "",
        "| Probe | What it proves | Result |",
        "| --- | --- | --- |",
    ]
    for result in results:
        lines.append(f"| {result.name} | {result.note} | {'PASS' if result.ok else 'FAIL'} |")
    lines.extend(
        [
            "",
            "A project environment note should record:",
            "",
            "1. which variables are exported to child processes;",
            "2. which startup file or project env file changed them;",
            "3. the PATH head before and after the project env is sourced;",
            "4. which variables are placeholders/examples and which are local-only values that must not be committed.",
        ]
    )
    (REPORTS / "environment_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    results = build_probes()
    (REPORTS / "env_profile_probe.json").write_text(
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
