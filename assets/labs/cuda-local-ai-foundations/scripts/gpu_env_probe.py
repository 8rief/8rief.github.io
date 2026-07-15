#!/usr/bin/env python3
"""Collect a public-safe local GPU/AI environment report.

The probe is deliberately read-only. Missing CUDA toolkit or Python packages are
reported as readiness gaps instead of hard failures, because the first teaching
post is about making the gap visible before installing anything.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PACKAGES = [
    "torch",
    "transformers",
    "peft",
    "trl",
    "bitsandbytes",
    "accelerate",
    "datasets",
    "numpy",
]


def run_command(cmd: list[str]) -> dict[str, Any]:
    exe = shutil.which(cmd[0])
    if exe is None:
        return {"available": False, "cmd": cmd, "stdout": "", "stderr": f"{cmd[0]} not found", "returncode": None}
    try:
        proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    except Exception as exc:  # intentionally recorded, not swallowed
        return {"available": True, "cmd": cmd, "stdout": "", "stderr": repr(exc), "returncode": -1}
    return {"available": True, "cmd": cmd, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip(), "returncode": proc.returncode}


def parse_nvidia_smi_csv(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    reader = csv.reader(line for line in text.splitlines() if line.strip())
    for row in reader:
        if len(row) >= 4:
            rows.append(
                {
                    "name": row[0].strip(),
                    "compute_capability": row[1].strip(),
                    "memory_total": row[2].strip(),
                    "driver_version": row[3].strip(),
                }
            )
    return rows


def package_status() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in PACKAGES:
        spec = importlib.util.find_spec(name)
        item: dict[str, Any] = {"installed": spec is not None, "version": None, "import_error": None}
        if spec is not None:
            try:
                module = __import__(name)
                item["version"] = getattr(module, "__version__", None)
                if name == "torch":
                    item["cuda_available"] = bool(module.cuda.is_available())
                    item["torch_cuda_version"] = getattr(module.version, "cuda", None)
                    if item["cuda_available"]:
                        item["device_name"] = module.cuda.get_device_name(0)
                        item["device_capability"] = ".".join(map(str, module.cuda.get_device_capability(0)))
                        item["arch_list"] = module.cuda.get_arch_list()
            except Exception as exc:  # imports may fail if binary deps are missing
                item["import_error"] = f"{type(exc).__name__}: {exc}"
        result[name] = item
    return result


def meminfo() -> dict[str, int]:
    data: dict[str, int] = {}
    path = Path("/proc/meminfo")
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        parts = rest.strip().split()
        if parts and parts[0].isdigit():
            data[key] = int(parts[0])
    return data


def readiness(report: dict[str, Any]) -> dict[str, Any]:
    gaps: list[str] = []
    gpu_seen = bool(report["gpu"].get("devices"))
    nvcc_ready = report["commands"]["nvcc_version"]["available"] and report["commands"]["nvcc_version"]["returncode"] == 0
    torch_info = report["python_packages"]["torch"]
    torch_ready = bool(torch_info.get("installed")) and bool(torch_info.get("cuda_available"))
    if not gpu_seen:
        gaps.append("nvidia_smi_gpu_not_seen")
    if not nvcc_ready:
        gaps.append("nvcc_missing_or_unusable")
    if not torch_ready:
        gaps.append("pytorch_cuda_missing_or_unusable")
    for pkg in ["transformers", "peft", "trl", "bitsandbytes", "accelerate", "datasets"]:
        if not report["python_packages"][pkg]["installed"]:
            gaps.append(f"python_package_missing:{pkg}")
    return {
        "gpu_visible": gpu_seen,
        "cuda_cpp_ready": gpu_seen and nvcc_ready,
        "pytorch_cuda_ready": gpu_seen and torch_ready,
        "gaps": gaps,
        "teaching_interpretation": "The machine can see an NVIDIA GPU, but CUDA C++ and local fine-tuning need toolkit/package setup before the later labs.",
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# CUDA 与本地小模型工程环境报告",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## 机器与GPU",
        "",
    ]
    devices = report["gpu"].get("devices", [])
    if devices:
        lines.append("| GPU | Compute capability | 显存 | Driver |")
        lines.append("| --- | --- | --- | --- |")
        for dev in devices:
            lines.append(f"| {dev['name']} | {dev['compute_capability']} | {dev['memory_total']} | {dev['driver_version']} |")
    else:
        lines.append("未通过 `nvidia-smi` 看到GPU。")
    lines += [
        "",
        "## 工具链状态",
        "",
        f"- `nvidia-smi`: `{report['commands']['nvidia_smi_query']['returncode']}`",
        f"- `nvcc`: {'available' if report['commands']['nvcc_version']['available'] else 'missing'}",
        f"- Python: `{report['python']['version']}`",
        "",
        "## Python包状态",
        "",
        "| Package | Installed | Version | CUDA/notes |",
        "| --- | --- | --- | --- |",
    ]
    for name, item in report["python_packages"].items():
        note = ""
        if name == "torch" and item.get("installed"):
            note = f"cuda_available={item.get('cuda_available')}, torch_cuda={item.get('torch_cuda_version')}"
        if item.get("import_error"):
            note = item["import_error"]
        lines.append(f"| {name} | {item['installed']} | {item.get('version') or ''} | {note} |")
    lines += [
        "",
        "## Readiness",
        "",
        f"- GPU visible: `{report['readiness']['gpu_visible']}`",
        f"- CUDA C++ ready: `{report['readiness']['cuda_cpp_ready']}`",
        f"- PyTorch CUDA ready: `{report['readiness']['pytorch_cuda_ready']}`",
        "- Gaps:",
    ]
    for gap in report["readiness"]["gaps"]:
        lines.append(f"  - `{gap}`")
    lines += [
        "",
        "## 解释",
        "",
        report["readiness"]["teaching_interpretation"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    nvidia_query = run_command([
        "nvidia-smi",
        "--query-gpu=name,compute_cap,memory.total,driver_version",
        "--format=csv,noheader",
    ])
    nvcc_version = run_command(["nvcc", "--version"])
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "meminfo_kb": meminfo(),
        },
        "python": {"version": platform.python_version(), "executable": shutil.which("python3") or shutil.which("python")},
        "commands": {"nvidia_smi_query": nvidia_query, "nvcc_version": nvcc_version},
        "gpu": {"devices": parse_nvidia_smi_csv(nvidia_query["stdout"]) if nvidia_query["returncode"] == 0 else []},
        "python_packages": package_status(),
    }
    report["readiness"] = readiness(report)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, args.markdown)
    print(f"gpu_visible={report['readiness']['gpu_visible']}")
    print(f"cuda_cpp_ready={report['readiness']['cuda_cpp_ready']}")
    print(f"pytorch_cuda_ready={report['readiness']['pytorch_cuda_ready']}")
    print(f"gaps={len(report['readiness']['gaps'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
