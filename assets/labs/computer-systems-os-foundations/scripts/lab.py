#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "systems_lab.c"
TMP = ROOT / ".lab_tmp"
REPORTS = ROOT / "reports"
BIN = TMP / "systems_lab"


def run(cmd: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def parse_key_values(text: str) -> dict[str, object]:
    values: dict[str, object] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        raw = raw.strip()
        if raw in {"true", "false"}:
            values[key] = raw == "true"
        elif re.fullmatch(r"-?\d+", raw):
            values[key] = int(raw)
        elif re.fullmatch(r"-?\d+\.\d+", raw):
            values[key] = float(raw)
        else:
            values[key] = raw
    return values


def make_svg(path: Path, title: str, nodes: list[str], footer: str) -> None:
    width = 920
    height = 230
    box_w = 150
    box_h = 64
    gap = 28
    x0 = 40
    y = 110
    colors = ["#e8f0fe", "#e6f4ea", "#fef7e0", "#fce8e6", "#f3e8fd"]
    def esc(s: object) -> str:
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f"<title>{esc(title)}</title>",
        f"<desc>{esc(' -> '.join(nodes))}</desc>",
        '<rect x="0" y="0" width="920" height="230" fill="#ffffff"/>',
        f'<text x="40" y="42" font-family="Arial, Microsoft YaHei, sans-serif" font-size="22" font-weight="700" fill="#202124">{esc(title)}</text>',
    ]
    for i, node in enumerate(nodes):
        x = x0 + i * (box_w + gap)
        out.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="14" fill="{colors[i % len(colors)]}" stroke="#5f6368" stroke-width="1.2"/>')
        if len(node) <= 14:
            lines = [node]
        else:
            lines = [node[:14], node[14:28]]
        for j, line in enumerate(lines):
            out.append(f'<text x="{x + box_w/2}" y="{y + 27 + j*20}" text-anchor="middle" font-family="Arial, Microsoft YaHei, sans-serif" font-size="14" fill="#202124">{esc(line)}</text>')
        if i < len(nodes) - 1:
            ax1 = x + box_w + 6
            ax2 = x + box_w + gap - 8
            ay = y + box_h / 2
            out.append(f'<line x1="{ax1}" y1="{ay}" x2="{ax2}" y2="{ay}" stroke="#5f6368" stroke-width="2"/>')
            out.append(f'<path d="M {ax2} {ay} L {ax2-8} {ay-5} L {ax2-8} {ay+5} Z" fill="#5f6368"/>')
    out.append(f'<text x="40" y="205" font-family="Arial, Microsoft YaHei, sans-serif" font-size="13" fill="#5f6368">{esc(footer)}</text>')
    out.append("</svg>")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def write_report(metrics: dict[str, object], output: str, gcc_version: str) -> None:
    report = f"""# Computer systems and OS foundations lab report

## Environment

- Python: {platform.python_version()}
- Platform: {platform.platform()}
- GCC: {gcc_version.splitlines()[0] if gcc_version else 'unknown'}

## Headline metrics

- Endianness observed little-endian: `{metrics['data_little_endian']}`
- `uint32_t` size: `{metrics['data_uint32_size']}` bytes
- Child process exit code: `{metrics['process_child_exit_code']}`
- File bytes written/read: `{metrics['fd_file_bytes_written']}` / `{metrics['fd_file_bytes_read']}`
- Page size: `{metrics['vm_page_size']}` bytes
- Copy-on-write parent unchanged: `{metrics['vm_cow_parent_unchanged']}`
- Controlled race expected/actual: `{metrics['thread_controlled_race_expected']}` / `{metrics['thread_controlled_race_actual']}`
- Mutex counter expected/actual: `{metrics['thread_mutex_expected']}` / `{metrics['thread_mutex_actual']}`
- Signal IPC message: `{metrics['signal_ipc_message']}`
- Cache row-major ns: `{metrics['cache_row_major_ns']}`
- Cache column-major ns: `{metrics['cache_column_major_ns']}`
- Cache column/row ratio: `{metrics['cache_column_to_row_ratio']}`

## Raw demo output

```text
{output.strip()}
```
"""
    (REPORTS / "report.md").write_text(report, encoding="utf-8")


def main() -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    compiler = shutil.which("gcc") or shutil.which("cc")
    if compiler is None:
        raise SystemExit("gcc_or_cc_not_found")
    gcc_version = run([compiler, "--version"]).stdout
    compile_cmd = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "-pthread", str(SRC), "-o", str(BIN)]
    run(compile_cmd)
    demo = run([str(BIN)])
    metrics = parse_key_values(demo.stdout)
    metrics["compiler"] = Path(compiler).name
    metrics["python_version"] = platform.python_version()
    metrics["platform"] = platform.platform()
    (REPORTS / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(metrics, demo.stdout, gcc_version)
    make_svg(REPORTS / "systems_flow.svg", "Systems foundations lab flow", ["bytes", "memory", "process", "fd/pipe", "vm/thread"], "The lab turns OS abstractions into observable command output.")
    make_svg(REPORTS / "memory_process_fd.svg", "Memory, process, fd model", ["address spaces", "fork/wait", "file descriptor", "pipe", "signal"], "Each abstraction is checked by a small user-space program.")
    make_svg(REPORTS / "cache_locality.svg", "Cache locality observation", ["matrix", "row scan", "column scan", "timing", "ratio"], "The exact ratio is machine-dependent; the measurement boundary is recorded.")
    summary = {
        "systems_os_status": metrics["systems_os_status"],
        "page_size": metrics["vm_page_size"],
        "mutex_correct": metrics["thread_mutex_correct"],
        "cache_column_to_row_ratio": metrics["cache_column_to_row_ratio"],
        "signal_ipc_message": metrics["signal_ipc_message"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
