#!/usr/bin/env python3
from __future__ import annotations

import json, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)
SRC.mkdir(exist_ok=True)

VECTOR_CU = r'''
#include <cuda_runtime.h>
#include <cstdio>

__global__ void vector_add(const float* a, const float* b, float* c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}

int main() {
    const int n = 16;
    float a[n], b[n], c[n];
    for (int i = 0; i < n; ++i) { a[i] = float(i); b[i] = float(2 * i); }
    float *da, *db, *dc;
    cudaMalloc(&da, n * sizeof(float));
    cudaMalloc(&db, n * sizeof(float));
    cudaMalloc(&dc, n * sizeof(float));
    cudaMemcpy(da, a, n * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(db, b, n * sizeof(float), cudaMemcpyHostToDevice);
    vector_add<<<(n + 7) / 8, 8>>>(da, db, dc, n);
    cudaMemcpy(c, dc, n * sizeof(float), cudaMemcpyDeviceToHost);
    cudaDeviceSynchronize();
    for (int i = 0; i < n; ++i) if (c[i] != a[i] + b[i]) return 2;
    std::printf("vector_add_ok n=%d last=%.1f\n", n, c[n-1]);
    cudaFree(da); cudaFree(db); cudaFree(dc);
    return 0;
}
'''.strip() + "\n"

REDUCTION_CU = r'''
#include <cuda_runtime.h>
#include <cstdio>

__global__ void block_sum(const float* x, float* partial, int n) {
    extern __shared__ float s[];
    int tid = threadIdx.x;
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    s[tid] = (i < n) ? x[i] : 0.0f;
    __syncthreads();
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (tid < stride) s[tid] += s[tid + stride];
        __syncthreads();
    }
    if (tid == 0) partial[blockIdx.x] = s[0];
}
'''.strip() + "\n"

(SRC / "vector_add.cu").write_text(VECTOR_CU)
(SRC / "block_reduction.cu").write_text(REDUCTION_CU)


def cpu_vector_add(n: int = 16) -> dict:
    a = [float(i) for i in range(n)]
    b = [float(2 * i) for i in range(n)]
    t0 = time.perf_counter()
    c = [x + y for x, y in zip(a, b)]
    elapsed_us = (time.perf_counter() - t0) * 1_000_000
    return {"n": n, "last": c[-1], "elapsed_us": elapsed_us, "correct": all(c[i] == 3 * i for i in range(n))}


def thread_map(n: int = 20, block_dim: int = 8) -> list[dict]:
    grid_dim = (n + block_dim - 1) // block_dim
    rows = []
    for block in range(grid_dim):
        for thread in range(block_dim):
            idx = block * block_dim + thread
            rows.append({"blockIdx.x": block, "threadIdx.x": thread, "global_i": idx, "active": idx < n})
    return rows


def memory_stride() -> list[dict]:
    base = 0
    elem_bytes = 4
    return [
        {"stride": stride, "thread_addresses": [base + (tid * stride) * elem_bytes for tid in range(8)]}
        for stride in [1, 2, 4, 8]
    ]


def reduction_steps(values: list[int] | None = None) -> list[dict]:
    if values is None:
        values = list(range(1, 9))
    steps = []
    current = values[:]
    stride = len(current) // 2
    while stride:
        before = current[:]
        for i in range(stride):
            current[i] += current[i + stride]
        steps.append({"stride": stride, "before": before, "after_active_prefix": current[:stride], "full_state": current[:]})
        stride //= 2
    return steps


def compile_vector_add() -> dict:
    nvcc = shutil.which("nvcc")
    if not nvcc:
        return {"status": "skipped", "reason": "nvcc not found", "source": str(SRC / "vector_add.cu")}
    out = ROOT / "reports" / "vector_add_cuda"
    cmd = [nvcc, "-O2", "-arch=sm_120", str(SRC / "vector_add.cu"), "-o", str(out)]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    run = None
    if proc.returncode == 0:
        run_proc = subprocess.run([str(out)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        run = {"returncode": run_proc.returncode, "stdout": run_proc.stdout.strip(), "stderr": run_proc.stderr.strip()}
    return {"status": "compiled" if proc.returncode == 0 else "compile_failed", "cmd": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "run": run}


report = {
    "cpu_vector_add": cpu_vector_add(),
    "thread_map": thread_map(),
    "memory_stride": memory_stride(),
    "reduction_steps": reduction_steps(),
    "cuda_compile": compile_vector_add(),
}
(REPORTS / "cuda_foundations_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
md = ["# CUDA foundations lab report", "", f"CPU vector add correct: `{report['cpu_vector_add']['correct']}`, last=`{report['cpu_vector_add']['last']}`.", "", "## Thread map", "", "| block | thread | global i | active |", "| --- | --- | --- | --- |"]
for row in report["thread_map"]:
    md.append(f"| {row['blockIdx.x']} | {row['threadIdx.x']} | {row['global_i']} | {row['active']} |")
md += ["", "## Stride addresses", "", "| stride | first 8 addresses |", "| --- | --- |"]
for row in report["memory_stride"]:
    md.append(f"| {row['stride']} | `{row['thread_addresses']}` |")
md += ["", "## Reduction", "", "| stride | active prefix after add |", "| --- | --- |"]
for row in report["reduction_steps"]:
    md.append(f"| {row['stride']} | `{row['after_active_prefix']}` |")
md += ["", "## CUDA compile", "", f"Status: `{report['cuda_compile']['status']}`", f"Reason: `{report['cuda_compile'].get('reason','')}`", ""]
(REPORTS / "cuda_foundations_report.md").write_text("\n".join(md))
print("cuda_foundations_ok", report["cpu_vector_add"]["correct"], report["cuda_compile"]["status"])
