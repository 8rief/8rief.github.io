#!/usr/bin/env python3
"""Collect a small, reproducible transcript for learning local documentation tools."""

from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


@dataclass(frozen=True)
class Probe:
    name: str
    argv: Sequence[str]
    contains: Sequence[str]
    note: str


@dataclass
class Result:
    name: str
    argv: list[str]
    returncode: int
    ok: bool
    expected_tokens: list[str]
    missing_tokens: list[str]
    first_lines: list[str]
    note: str


PROBES: list[Probe] = [
    Probe(
        name="version-boundary",
        argv=["python3", "--version"],
        contains=["Python"],
        note="A reproducible note starts by recording the tool version that the later command behavior belongs to.",
    ),
    Probe(
        name="help-option",
        argv=["/usr/bin/printf", "--help"],
        contains=["Usage:", "FORMAT"],
        note="`--help` is fast and command-local; it is usually enough to confirm options and invocation shape.",
    ),
    Probe(
        name="apropos-search",
        argv=["man", "-k", "^printf$"],
        contains=["printf (1)", "printf (3)"],
        note="`man -k` searches the whatis database and helps distinguish command-section and library-section pages.",
    ),
    Probe(
        name="manual-page",
        argv=["sh", "-lc", "man 1 printf | col -b | sed -n '1,16p'"],
        contains=["PRINTF(1)", "SYNOPSIS"],
        note="A manual page gives the stable contract: name, synopsis, description, options, examples, files, and related pages.",
    ),
    Probe(
        name="large-help-filter",
        argv=["sh", "-lc", "curl --help all | grep -F -- '--fail-with-body'"],
        contains=["--fail-with-body", "HTTP errors"],
        note="Large help output should be filtered to the option under investigation, while the full command is kept in the transcript.",
    ),
    Probe(
        name="python-module-doc",
        argv=["sh", "-lc", "python3 -m pydoc pathlib | grep -m1 -E 'class Path|class PurePath'"],
        contains=["class Path"],
        note="Language ecosystems often provide local module docs; `pydoc` is the Python analogue for quick API orientation.",
    ),
    Probe(
        name="subcommand-help",
        argv=["python3", "-m", "pip", "--help"],
        contains=["Usage:", "Commands:"],
        note="Tools with subcommands usually have layered help: top-level help first, then `tool subcommand --help`.",
    ),
]


def run_probe(probe: Probe) -> Result:
    completed = subprocess.run(
        list(probe.argv),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=8.0,
        check=False,
    )
    output = completed.stdout.replace("\r\n", "\n")
    missing = [token for token in probe.contains if token not in output]
    return Result(
        name=probe.name,
        argv=list(probe.argv),
        returncode=completed.returncode,
        ok=completed.returncode == 0 and not missing,
        expected_tokens=list(probe.contains),
        missing_tokens=missing,
        first_lines=output.splitlines()[:8],
        note=probe.note,
    )


def write_transcript(results: list[Result]) -> None:
    lines = ["# Local documentation workflow transcript", ""]
    for result in results:
        shell = " ".join(shlex.quote(part) for part in result.argv)
        lines.extend(
            [
                f"## {result.name}",
                "",
                f"command: `{shell}`",
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


def write_learning_check(results: list[Result]) -> None:
    lines = [
        "# Learning check",
        "",
        "| Step | Command boundary | What the output proves | Status |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result.name} | `{' '.join(shlex.quote(x) for x in result.argv)}` | "
            f"{result.note} | {'PASS' if result.ok else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "A learner should be able to answer three questions from this report:",
            "",
            "1. Which exact tool/version did I inspect?",
            "2. Which local documentation source answered the question?",
            "3. Which output line is the evidence, not just my memory of the command?",
        ]
    )
    (REPORTS / "learning_check.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    results = [run_probe(probe) for probe in PROBES]
    (REPORTS / "doc_probe.json").write_text(
        json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_transcript(results)
    write_learning_check(results)
    failed = [result.name for result in results if not result.ok]
    print(json.dumps({"probes": len(results), "failed": failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
