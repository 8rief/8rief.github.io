# hardware-bottleneck-foundations

配套文章：**硬件瓶颈实测第一课：cache、branch、PCIe 和 CUDA timing 怎么一步步看**。

这个 lab 面向第一次做性能实验的学习者。它先用 CPU 必跑实验观察 cache locality、stride 和 branch predictability；如果本机有 `nvcc` 和可用 NVIDIA GPU，再用可选 CUDA 程序观察 host/device transfer 与 kernel event timing。

## 运行前你需要知道什么

- 必需：WSL/Linux、`bash`、`gcc`、`python3`。
- 可选：NVIDIA driver、CUDA toolkit 的 `nvcc`、可用 GPU。
- 没有 CUDA toolkit 时不是失败：脚本会把 CUDA 部分写成 `skipped`，CPU 实验仍然完整运行。

## 一步步运行

如果你从公开博客仓库运行：

```bash
cd ~/8rief.github.io
cd assets/labs/hardware-bottleneck-foundations
bash run_lab.sh
```

如果你在本地 canonical lab 目录运行，也可以直接：

```bash
bash run_lab.sh
```

这几条命令分别做了什么：

1. `cd ...`：进入实验目录，确保生成物只写在当前 lab 下。
2. `bash run_lab.sh`：清理旧的 `.lab_tmp/` 与 `reports/`，编译 C benchmark，运行 CPU 实验，尝试可选 CUDA 实验，生成报告并运行测试。

## 如果 CUDA 被 skipped，怎样补齐 nvcc

WSL 里的 NVIDIA driver 来自 Windows 侧映射；在 Ubuntu/WSL 里不要安装 Linux display driver。这个 lab 提供了一个无 sudo 的学习路径：只把 CUDA toolkit 安装到用户目录，用来获得 `nvcc`、headers 和 runtime 库。

```bash
cd ~/8rief.github.io/assets/labs/hardware-bottleneck-foundations
bash scripts/setup_cuda_runfile_user.sh
source .tools/cuda-env.sh
bash run_lab.sh
```

这些命令分别做了什么：

1. `setup_cuda_runfile_user.sh` 下载 NVIDIA CUDA runfile，校验 MD5，只执行 toolkit 安装，不安装 driver。
2. 默认安装目录是 `$HOME/.local/cuda-13.2.1`；下载包约 4GB，展开后的 toolkit 约 7GB。
3. `.tools/cuda-env.sh` 是本机生成的环境文件，不属于公开源码；它把 `CUDA_HOME`、`PATH`、`LD_LIBRARY_PATH` 和 `CUDA_ARCH_FLAGS=-arch=native` 设好。
4. `source .tools/cuda-env.sh` 只影响当前 shell，让后面的 `bash run_lab.sh` 能找到用户目录里的 `nvcc`。
5. `CUDA_ARCH_FLAGS=-arch=native` 让 `nvcc` 针对当前 GPU 生成代码，避免第一次运行因为 PTX JIT 混入计时。

如果你的机器已经有系统级 `nvcc`，可以不运行安装脚本，直接设置目标架构后运行：

```bash
export CUDA_ARCH_FLAGS=-arch=native
bash run_lab.sh
```

## 你会看到什么文件

- `reports/raw_metrics.csv`：C 程序输出的 CPU 原始测量行。
- `reports/cuda_transfer_report.json`：如果有 `nvcc` 和可用 GPU，会记录 pageable/pinned host-device copy 与 kernel timing；否则写明 skipped/原因。
- `reports/report.json`：汇总后的结构化报告，适合写脚本读取。
- `reports/report.md`：给学习者阅读的解释版报告。
- `reports/run_lab_output.txt`：完整终端输出，方便你回看。
- `src/hardware_bottleneck_lab.c` 和 `src/cuda_transfer_probe.cu`：分别对应 CPU 必跑实验和可选 CUDA timing 实验。

## 输出怎么读

阅读重点是“同一台机器、同一条命令”下不同访问模式的相对关系，不需要背某个固定数字：

```text
MATRIX_COLUMN_TO_ROW_RATIO=...
BRANCH_UNPREDICTABLE_TO_PREDICTABLE_RATIO=...
CUDA_STATUS=ok|skipped|compile_failed|run_failed
RUN_STATUS=ok
```

- `MATRIX_COLUMN_TO_ROW_RATIO > 1`：按列访问比按行访问慢，说明 row-major 数据布局和 cache line 利用率影响了运行时间。
- `BRANCH_UNPREDICTABLE_TO_PREDICTABLE_RATIO`：只说明这次本机分支实验的相对耗时；不能强行推出所有随机分支都更慢。
- `CUDA_STATUS=skipped`：说明当前环境没有满足可选 CUDA 条件，不影响 CPU 部分学习目标；按上一节补齐 `nvcc` 后应重新运行。
- `CUDA_STATUS=ok`：说明 CUDA probe 编译并运行成功，`reports/cuda_transfer_report.json` 会包含 GPU 名称、pageable/pinned copy 时间和 kernel event 时间。
- `RUN_STATUS=ok`：报告生成成功，测试也通过。

## 一次 RTX 5070 真实 CUDA 输出怎么读

补齐用户态 toolkit 后，本机一次运行得到 `CUDA_STATUS=ok`，GPU 为 `NVIDIA GeForce RTX 5070`。节选结果如下：

```text
bytes=1048576   pageable_h2d_ms=0.1637  pinned_h2d_ms=0.0671  kernel_ms=0.0345
bytes=8388608   pageable_h2d_ms=0.9021  pinned_h2d_ms=0.2460  kernel_ms=0.0468
bytes=33554432  pageable_h2d_ms=4.4474  pinned_h2d_ms=0.9834  kernel_ms=0.1862
```

这说明在这个简单 kernel 上，32MiB pageable H2D+D2H 拷贝约 `8.86ms`，pinned H2D+D2H 约 `1.99ms`，而 kernel event 时间约 `0.19ms`。所以如果端到端任务每次都要来回搬一大块数据，优化 kernel 本身不一定先改变用户感知时间。先拆分 copy 与 kernel，再讨论优化。

## 实验边界

这些数字是本机证据，不是跨机器 benchmark。它们用于训练瓶颈判断顺序：访问顺序、cache line 利用率、分支可预测性、传输与 kernel 计时是否应分开看。更严格的性能结论需要固定 CPU/GPU 频率、warm-up、多次重复、硬件计数器或 profiler。
