#!/usr/bin/env python3
"""Generate a small Bash error-handling lab and record stable evidence."""
from __future__ import annotations

import json
import os
import re
import shutil
import shlex
import stat
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from textwrap import dedent

LAB_DIR = Path("/tmp/script-error-lab")
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


@dataclass
class CommandResult:
    name: str
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


def write_executable(path: Path, content: str) -> None:
    path.write_text(dedent(content).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def run(name: str, argv: list[str], cwd: Path = LAB_DIR) -> CommandResult:
    proc = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CommandResult(name, argv, proc.returncode, proc.stdout, proc.stderr)


def setup_lab() -> dict[str, Path]:
    if LAB_DIR.exists():
        shutil.rmtree(LAB_DIR)
    (LAB_DIR / "bin").mkdir(parents=True)
    (LAB_DIR / "work").mkdir()
    (LAB_DIR / "work" / "data.txt").write_text("needle\nalpha beta\n", encoding="utf-8")

    scripts = {
        "args": LAB_DIR / "bin" / "args_demo.sh",
        "exit": LAB_DIR / "bin" / "exit_status_demo.sh",
        "strict": LAB_DIR / "bin" / "strict_demo.sh",
        "trap": LAB_DIR / "bin" / "trap_cleanup_demo.sh",
        "usage": LAB_DIR / "bin" / "usage_demo.sh",
    }

    write_executable(
        scripts["args"],
        r'''
        #!/usr/bin/env bash
        set -u
        printf 'SCRIPT_NAME=%s\n' "$0"
        printf 'ARG_COUNT=%s\n' "$#"
        printf 'FIRST_ARG=%s\n' "${1-<missing>}"
        printf 'ALL_ARGS='
        for arg in "$@"; do
          printf '[%s]' "$arg"
        done
        printf '\n'
        while (($#)); do
          printf 'SHIFT_ARG=%s REMAINING_BEFORE=%s\n' "$1" "$#"
          shift
        done
        printf 'ARG_COUNT_AFTER_SHIFT=%s\n' "$#"
        ''',
    )

    write_executable(
        scripts["exit"],
        r'''
        #!/usr/bin/env bash
        set -u
        data_file=${1:-work/data.txt}
        true
        printf 'true rc=%s\n' "$?"
        if grep -q 'needle' "$data_file"; then
          printf 'grep needle rc=0 action=found\n'
        else
          rc=$?
          printf 'grep needle rc=%s action=missing\n' "$rc"
        fi
        if grep -q 'missing' "$data_file"; then
          printf 'grep missing rc=0 action=found\n'
        else
          rc=$?
          printf 'grep missing rc=%s action=not-found-expected\n' "$rc"
        fi
        false || rc=$?
        printf 'false rc captured=%s\n' "$rc"
        ''',
    )

    write_executable(
        scripts["strict"],
        r'''
        #!/usr/bin/env bash
        set -euo pipefail
        mode=${1:-pass}
        data_file=work/data.txt
        case "$mode" in
          pass)
            printf 'STRICT_PASS=start\n'
            grep -q 'needle' "$data_file"
            printf 'STRICT_PASS=done\n'
            ;;
          fail-command)
            printf 'STRICT_FAIL=before-command\n'
            grep -q 'missing' "$data_file"
            printf 'STRICT_FAIL=unreached\n'
            ;;
          fail-unset)
            printf 'STRICT_UNSET=before\n'
            printf '%s\n' "$UNSET_STRICT_DEMO"
            printf 'STRICT_UNSET=unreached\n'
            ;;
          fail-pipe)
            printf 'STRICT_PIPE=before\n'
            printf 'alpha\nbeta\n' | grep -q 'missing' | wc -l
            printf 'STRICT_PIPE=unreached\n'
            ;;
          *)
            printf 'usage: strict_demo.sh [pass|fail-command|fail-unset|fail-pipe]\n' >&2
            exit 64
            ;;
        esac
        ''',
    )

    write_executable(
        scripts["trap"],
        r'''
        #!/usr/bin/env bash
        set -euo pipefail
        tmp=$(mktemp /tmp/script-error-trap.XXXXXX)
        cleanup() {
          local rc=$?
          rm -f "$tmp"
          if [[ -e "$tmp" ]]; then
            printf 'cleanup_exists_after=yes\n'
          else
            printf 'cleanup_exists_after=no\n'
          fi
          return "$rc"
        }
        trap cleanup EXIT
        printf 'cleanup_file=%s\n' "$tmp"
        printf 'cleanup_exists_before=%s\n' "$(test -e "$tmp" && printf yes || printf no)"
        case "${1:-ok}" in
          ok)
            printf 'trap_mode=ok\n'
            ;;
          fail)
            printf 'trap_mode=fail\n'
            exit 7
            ;;
          *)
            printf 'usage: trap_cleanup_demo.sh [ok|fail]\n' >&2
            exit 64
            ;;
        esac
        ''',
    )

    write_executable(
        scripts["usage"],
        r'''
        #!/usr/bin/env bash
        set -u
        usage() {
          printf 'usage: %s <input-file> <output-file>\n' "$(basename "$0")" >&2
        }
        if [[ "$#" -ne 2 ]]; then
          usage
          exit 64
        fi
        input=$1
        output=$2
        if [[ ! -f "$input" ]]; then
          printf 'error: input not found: %s\n' "$input" >&2
          exit 66
        fi
        cp "$input" "$output"
        printf 'copied input=%s output=%s bytes=%s\n' "$input" "$output" "$(wc -c < "$output")"
        ''',
    )
    return scripts


def assert_contains(text: str, token: str, name: str) -> None:
    if token not in text:
        raise AssertionError(f"{name}: expected token {token!r} not found in {text!r}")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    scripts = setup_lab()
    results = [
        run("args-three", [str(scripts["args"]), "alpha", "two words", "--flag"]),
        run("exit-status", [str(scripts["exit"]), "work/data.txt"]),
        run("strict-pass", [str(scripts["strict"]), "pass"]),
        run("strict-fail-command", [str(scripts["strict"]), "fail-command"]),
        run("strict-fail-unset", [str(scripts["strict"]), "fail-unset"]),
        run("strict-fail-pipe", [str(scripts["strict"]), "fail-pipe"]),
        run("trap-fail", [str(scripts["trap"]), "fail"]),
        run("usage-missing", [str(scripts["usage"])]),
        run("usage-ok", [str(scripts["usage"]), "work/data.txt", "work/copied.txt"]),
    ]

    by_name = {r.name: r for r in results}
    assert by_name["args-three"].returncode == 0
    assert_contains(by_name["args-three"].stdout, "ARG_COUNT=3", "args-three")
    assert_contains(by_name["args-three"].stdout, "ALL_ARGS=[alpha][two words][--flag]", "args-three")
    assert_contains(by_name["args-three"].stdout, "ARG_COUNT_AFTER_SHIFT=0", "args-three")

    assert by_name["exit-status"].returncode == 0
    assert_contains(by_name["exit-status"].stdout, "grep missing rc=1", "exit-status")
    assert_contains(by_name["exit-status"].stdout, "false rc captured=1", "exit-status")

    assert by_name["strict-pass"].returncode == 0
    assert_contains(by_name["strict-pass"].stdout, "STRICT_PASS=done", "strict-pass")
    assert by_name["strict-fail-command"].returncode == 1
    assert_contains(by_name["strict-fail-command"].stdout, "STRICT_FAIL=before-command", "strict-fail-command")
    assert by_name["strict-fail-unset"].returncode != 0
    assert "unbound variable" in by_name["strict-fail-unset"].stderr
    assert by_name["strict-fail-pipe"].returncode == 1

    assert by_name["trap-fail"].returncode == 7
    assert_contains(by_name["trap-fail"].stdout, "cleanup_exists_after=no", "trap-fail")
    tmp_match = re.search(r"cleanup_file=(\S+)", by_name["trap-fail"].stdout)
    assert tmp_match, by_name["trap-fail"].stdout
    assert not Path(tmp_match.group(1)).exists()

    assert by_name["usage-missing"].returncode == 64
    assert "usage:" in by_name["usage-missing"].stderr
    assert by_name["usage-ok"].returncode == 0
    assert_contains(by_name["usage-ok"].stdout, "copied input=work/data.txt", "usage-ok")

    report = {
        "lab_dir": str(LAB_DIR),
        "scripts": {key: str(value) for key, value in scripts.items()},
        "summary": {
            "args_count": 3,
            "grep_missing_rc": 1,
            "strict_failed_rc": by_name["strict-fail-command"].returncode,
            "strict_unset_rc": by_name["strict-fail-unset"].returncode,
            "strict_pipe_rc": by_name["strict-fail-pipe"].returncode,
            "trap_failed_rc": by_name["trap-fail"].returncode,
            "cleanup_exists_after": "no",
            "usage_missing_rc": by_name["usage-missing"].returncode,
            "usage_ok_rc": by_name["usage-ok"].returncode,
        },
        "commands": [asdict(r) for r in results],
    }
    (REPORTS / "script_error_probe.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    transcript_lines = [
        "# Linux script argument and error-handling lab transcript",
        "",
        f"Lab directory: `{LAB_DIR}`",
        "",
    ]
    for result in results:
        transcript_lines.append(f"## {result.name}")
        transcript_lines.append("")
        transcript_lines.append("```bash")
        transcript_lines.append(shlex.join(result.argv))
        transcript_lines.append(f"# rc={result.returncode}")
        transcript_lines.append("```")
        if result.stdout:
            transcript_lines.append("")
            transcript_lines.append("stdout:")
            transcript_lines.append("```text")
            transcript_lines.append(result.stdout.rstrip())
            transcript_lines.append("```")
        if result.stderr:
            transcript_lines.append("")
            transcript_lines.append("stderr:")
            transcript_lines.append("```text")
            transcript_lines.append(result.stderr.rstrip())
            transcript_lines.append("```")
        transcript_lines.append("")

    transcript_lines.extend(
        [
            "## Stable summary tokens",
            "",
            "```text",
            "ARG_COUNT=3",
            "grep missing rc=1",
            f"STRICT_FAILED rc={by_name['strict-fail-command'].returncode}",
            f"STRICT_UNSET rc={by_name['strict-fail-unset'].returncode}",
            f"STRICT_PIPE rc={by_name['strict-fail-pipe'].returncode}",
            "cleanup_exists_after=no",
            "usage: usage_demo.sh <input-file> <output-file>",
            "```",
            "",
        ]
    )
    (REPORTS / "transcript.md").write_text("\n".join(transcript_lines), encoding="utf-8")

    summary = dedent(
        f"""
        # Error-handling lab summary

        - Positional arguments preserve spaces when iterated as `"$@"`: `ARG_COUNT=3`, `ALL_ARGS=[alpha][two words][--flag]`.
        - `grep` returning 1 is a normal not-found status in an `if` condition: `grep missing rc=1`.
        - `set -euo pipefail` turns an unchecked missing grep, unset variable, or failed pipeline into an immediate nonzero script exit: command rc `{by_name['strict-fail-command'].returncode}`, unset rc `{by_name['strict-fail-unset'].returncode}`, pipe rc `{by_name['strict-fail-pipe'].returncode}`.
        - `trap cleanup EXIT` removed the temporary file even when the script exited with rc `{by_name['trap-fail'].returncode}`: `cleanup_exists_after=no`.
        - Explicit usage checks produce a predictable user error: missing arguments returned rc `{by_name['usage-missing'].returncode}` and printed `usage: usage_demo.sh <input-file> <output-file>`.
        """
    ).strip() + "\n"
    (REPORTS / "error_handling_summary.md").write_text(summary, encoding="utf-8")

    print("SCRIPT_ERROR_LAB_STATUS ok")
    print(f"lab_dir={LAB_DIR}")
    print("ARG_COUNT=3")
    print("grep missing rc=1")
    print(f"STRICT_FAILED rc={by_name['strict-fail-command'].returncode}")
    print(f"STRICT_UNSET rc={by_name['strict-fail-unset'].returncode}")
    print(f"STRICT_PIPE rc={by_name['strict-fail-pipe'].returncode}")
    print("cleanup_exists_after=no")
    print("usage: usage_demo.sh <input-file> <output-file>")
    print("reports=script_error_probe.json transcript.md error_handling_summary.md")


if __name__ == "__main__":
    main()
