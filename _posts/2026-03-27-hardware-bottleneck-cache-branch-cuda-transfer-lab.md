---
layout: post
title: "硬件瓶颈实测第一课：cache、branch、PCIe 和 CUDA timing 怎么一步步看"
date: 2026-03-27 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个 WSL 可运行实验，把 CPU cache locality、stride、branch predictability、host/device transfer 和 kernel timing 连成初学者能看懂的瓶颈证据链。"
tags: [hardware, microarchitecture, cache, branch-prediction, cuda, pci-e, performance, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/hardware-bottleneck-foundations/README.md`](/assets/labs/hardware-bottleneck-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
上一篇[硬件瓶颈地图](/computer-science-teaching/2026/03/26/hardware-bottleneck-map-cpu-memory-gpu.html)把问题分成 compute-bound、memory-bound、latency-bound、communication-bound 和 capacity-bound。地图能帮助你提问，但真正开始优化前，还需要一件事：**把瓶颈变成能复跑的证据**。

这篇文章只做一个小实验包。它不会给出“你的机器比我的机器快几倍”这种结论；它训练的是初学者的观察顺序：先跑命令，保存原始结果，再解释为什么访问顺序、cache line、分支路径、host/device 传输和 kernel timing 会影响一个程序。

## 为什么需要实测瓶颈

硬件瓶颈分析用来解决一个核心问题：性能问题经常同时跨过代码、编译器、CPU cache、内存带宽、GPU 传输和 kernel 执行。只凭直觉很容易把慢归因到最显眼的模块。可复跑实验先把观察对象切小，再把原始输出、环境条件和解释分开，让后续优化建立在证据上。

## 学习目标

读完并跑完实验后，你应该能做到：

1. 用 row-major 和 column-major 的对比解释 spatial locality。
2. 用 stride scan 解释为什么“读取的元素数变少”不等于“程序按比例变快”。
3. 用 branch predictability 实验理解“控制流也可能成为瓶颈”，同时知道本机结果不能替代 profiling。
4. 把 CUDA 计时拆成 host/device copy 和 kernel timing，而不是用一次端到端时间猜 kernel 是否变快。
5. 把这些证据连接到本地小模型：tokenizer、batch、sequence、KV cache、CPU↔GPU 搬运和显存预算。

## 先运行实验

如果你已经克隆过本站仓库，在 WSL 终端执行：

```bash
cd ~/8rief.github.io
git pull --ff-only
cd assets/labs/hardware-bottleneck-foundations
bash run_lab.sh
```

这四行分别做了什么：

1. `cd ~/8rief.github.io`：进入你本地的公开博客仓库。
2. `git pull --ff-only`：更新到远端最新版本，只允许快进，避免把学习实验和你自己的提交混在一起。
3. `cd assets/labs/hardware-bottleneck-foundations`：进入本篇文章配套实验目录。
4. `bash run_lab.sh`：编译 C benchmark，运行 CPU 实验；如果系统有 `nvcc` 和可用 GPU，再运行可选 CUDA transfer/timing probe；最后生成 JSON/Markdown 报告并跑测试。

如果你还没有克隆仓库：

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/hardware-bottleneck-foundations
bash run_lab.sh
```

这个实验只在当前目录生成 `reports/` 和 `.lab_tmp/`。它不会安装软件包，不会修改你的 home 目录，也不会下载模型。

## 你应该看到什么输出

第一次只跑 `bash run_lab.sh` 时，如果你的 WSL 还没有 `nvcc`，会看到 `CUDA_STATUS=skipped`。这不是失败，意思是 CPU cache/stride/branch 部分已经完成，但 CUDA C++ 编译器还没就绪。

本机补齐用户态 CUDA toolkit 后，同一个实验实际跑出了类似输出：

```text
nvcc=$HOME/.local/cuda-13.2.1/bin/nvcc
cuda_arch_flags=-arch=native
matrix_locality,row_major,...,0.004118781,19423.222,...
matrix_locality,column_major,...,0.024130916,3315.249,...
...
MATRIX_COLUMN_TO_ROW_RATIO=5.859
BRANCH_UNPREDICTABLE_TO_PREDICTABLE_RATIO=0.644
CUDA_STATUS=ok
RUN_STATUS=ok
hardware_bottleneck_lab_status=ok
```

第一条重要事实：同样是把 `1024×1024` 的 `double` 矩阵加起来，按行访问比按列访问快很多。本机这次 column/row 时间比约为 `5.859`。这个数字只说明：在这个程序、这个编译器、这台机器上，访问顺序足以主导运行时间；它不能当作跨机器 benchmark。

第二条重要事实：`BRANCH_UNPREDICTABLE_TO_PREDICTABLE_RATIO` 这次小于 1，说明这个教学 microbenchmark 不能被机械解释成“随机分支一定更慢”。编译器、CPU 预测器、数据依赖、WSL 调度和测量时长都可能改变这个比值。正确做法是把它当成观察入口，而不是当成结论口号。

第三条重要事实：`CUDA_STATUS=ok` 只证明 CUDA probe 编译并运行成功，不自动证明 GPU 加速了整个任务。真正需要解释的是 `reports/cuda_transfer_report.json` 里 copy 和 kernel 的分项时间。

## 把 CUDA skipped 变成 ok：WSL 里只补 toolkit

WSL 的 CUDA 边界容易装错。NVIDIA 和 Ubuntu 的 WSL 文档都强调：WSL 里的 CUDA driver 来自 Windows 侧 NVIDIA driver 映射，不要在 Ubuntu/WSL 里安装 Linux display driver。我们需要的是 CUDA toolkit：`nvcc`、headers、runtime 库和编译工具。

如果你有 sudo，官方推荐路径通常是 WSL-Ubuntu 的 `cuda-toolkit-<version>` 包。这个实验还提供了一条无 sudo 的学习路径：用 NVIDIA runfile 只安装 toolkit 到用户目录，不碰 driver。

在 WSL 终端执行：

```bash
cd ~/8rief.github.io/assets/labs/hardware-bottleneck-foundations
bash scripts/setup_cuda_runfile_user.sh
source .tools/cuda-env.sh
bash run_lab.sh
```

逐行解释：

1. `cd ...` 进入实验目录，让后续生成的 `.tools/` 和 `reports/` 都留在 lab 下。
2. `bash scripts/setup_cuda_runfile_user.sh` 下载 CUDA 13.2.1 Linux runfile，校验 MD5，然后执行 `--toolkit --toolkitpath=$HOME/.local/cuda-13.2.1 --no-man-page --override`。脚本不安装 driver。
3. runfile 下载约 4GB，用户目录 toolkit 展开后约 7GB。慢是正常的；这一步是在补齐 C++ 编译工具，不是在跑 benchmark。
4. `source .tools/cuda-env.sh` 把当前 shell 的 `CUDA_HOME`、`PATH`、`LD_LIBRARY_PATH` 和 `CUDA_ARCH_FLAGS` 设好。它不会永久修改你的 shell 配置。
5. `bash run_lab.sh` 重新跑实验。此时脚本能找到 `nvcc`，会编译 `src/cuda_transfer_probe.cu`。

为什么脚本默认设置 `CUDA_ARCH_FLAGS=-arch=native`？因为性能实验不想把第一次运行的 PTX JIT 编译成本混进 kernel timing。让 `nvcc` 针对当前 GPU 生成代码，配合程序里的 warm-up，可以让表格更接近 copy/kernel 本身的时间。换 GPU 或换 toolkit 后仍应重新运行，而不是复用我的数字。

## 实验目录里有什么

```text
hardware-bottleneck-foundations/
├── README.md
├── references.json
├── run_lab.sh
├── scripts/
│   └── report.py
├── src/
│   ├── hardware_bottleneck_lab.c
│   └── cuda_transfer_probe.cu
└── tests/
    └── test_report.py
```

- `hardware_bottleneck_lab.c`：CPU 必跑实验，包含 matrix locality、stride scan 和 branch predictability。
- `cuda_transfer_probe.cu`：可选 CUDA 实验，测 pageable/pinned host-device copy 和一个简单 kernel 的 CUDA event 时间。
- `report.py`：把原始 CSV 和 CUDA JSON 汇总成 `report.json` 与 `report.md`。
- `test_report.py`：检查报告结构、关键实验行和 CUDA status 是否明确。

注意这里没有把运行结果提交进仓库。`reports/` 应该由你在自己的机器上生成，因为它包含机器相关时间和本地环境信息。

## 原理一：为什么按行访问更快

C 的二维数组通常按 row-major 布局：同一行的相邻元素在内存中连续。CPU 访问内存时，会把一段连续字节搬进 cache line，而不是只搬当前这个 `double`。按行访问时，程序刚用完一个元素，很可能马上用同一个 cache line 里的下一个元素。

按列访问时，访问模式变成：

```text
a[0][0] -> a[1][0] -> a[2][0] -> ...
```

相邻两次访问在内存里隔了整整一行。CPU 仍然搬 cache line，但你的程序只用了其中很少一部分。这个现象会降低有效吞吐。

这就是微机原理里“存储层级”的实际用法：寄存器最快但最小，L1/L2/L3 cache 更大但更慢，DRAM 更大也更慢。优化的关键是让数据访问顺序尽量配合层级结构，层级名字只是理解这个过程的索引。

## 原理二：stride scan 看的是 cache line 利用率

实验里还有一组 stride scan：

```text
stride_scan,stride_1,...,11713.335 MiB/s
stride_scan,stride_8,...,3739.955 MiB/s
stride_scan,stride_32,...,2194.166 MiB/s
```

`stride_1` 表示每个元素都访问。`stride_32` 表示每隔 32 个 `double` 访问一个元素。看起来访问次数少了，程序应该更轻松；但从“有用字节吞吐”看，高 stride 可能更差。

原因是 CPU 仍然围绕 cache line 搬数据。假设一个 cache line 是 64 字节，它能放 8 个 `double`。`stride_1` 通常能用上这 8 个元素；`stride_8` 可能每条 cache line 只用一个元素；更大的 stride 还会让硬件预取器更难帮忙。程序读到的有用字节少了，但内存系统搬运和等待的成本没有按同样比例下降。

这件事会直接影响 CUDA 学习。GPU global memory 也奖励相邻线程访问连续地址。一个 warp 内线程访问连续位置，硬件更容易合并内存事务；如果线程各跳各的，吞吐会下降。

## 原理三：branch 实验为什么不能强行套结论

实验也测了 predictable 和 pseudo-random branch：

```text
BRANCH_UNPREDICTABLE_TO_PREDICTABLE_RATIO=1.001
```

这次本机结果里，随机分支和可预测分支几乎一样慢；另一次运行也可能出现随机分支略快或略慢。这个结果很有教学价值：**微架构规律不是口号，必须用本机证据校验。**

可能原因包括：

- 编译器把分支改写成了更容易执行的形式。
- CPU 分支预测、乱序执行和数据依赖共同影响结果。
- WSL、频率调度、缓存状态和测量时长会影响小实验。
- 两个分支体的算术依赖并不完全等价。

所以这组实验的正确用法是提出可验证问题：控制流是否可能进入瓶颈？如果怀疑是，就要用 perf、profile、硬件计数器或更严格的 microbenchmark 继续验证。

## 原理四：CUDA timing 必须拆开看

可选 CUDA 程序做三件事：

1. 分配 pageable host memory、pinned host memory 和 device memory。
2. 分别测 Host→Device、Device→Host 拷贝时间。
3. 对 device memory 上的数组运行一个简单 kernel，并用 CUDA event 测 kernel 时间。

这样拆分是为了避免一个常见误判：只看端到端时间，然后把慢全部归因到 kernel。对小任务来说，host/device copy、kernel launch、同步和数据准备可能比 kernel 本身更显著。NVIDIA 的 Best Practices Guide 也把 timing、bandwidth、host-device transfer、pinned memory 和 memory optimization 分开讨论。

如果你的 `reports/cuda_transfer_report.json` 是 `ok`，会看到类似结构。本机 RTX 5070 的一次真实输出节选如下：

```json
{
  "status": "ok",
  "device": "NVIDIA GeForce RTX 5070",
  "timing_note": "CUDA context was initialized before timed rows; each row also performs untimed copy/kernel warmup before event timing.",
  "rows": [
    {
      "bytes": 1048576,
      "pageable_h2d_ms": 0.1637,
      "pageable_d2h_ms": 0.1492,
      "pinned_h2d_ms": 0.0671,
      "pinned_d2h_ms": 0.0581,
      "kernel_ms": 0.0345
    },
    {
      "bytes": 8388608,
      "pageable_h2d_ms": 0.9021,
      "pageable_d2h_ms": 0.9179,
      "pinned_h2d_ms": 0.2460,
      "pinned_d2h_ms": 0.2917,
      "kernel_ms": 0.0468
    },
    {
      "bytes": 33554432,
      "pageable_h2d_ms": 4.4474,
      "pageable_d2h_ms": 4.4124,
      "pinned_h2d_ms": 0.9834,
      "pinned_d2h_ms": 1.0030,
      "kernel_ms": 0.1862
    }
  ]
}
```

这里的数值会因机器而变。你要比较的是同一机器、同一命令、同一输入大小下不同阶段的相对关系，而不是把一次结果当作通用性能结论。

以 32MiB 那一行为例，pageable H2D+D2H 约 `8.86ms`，pinned H2D+D2H 约 `1.99ms`，kernel event 时间约 `0.19ms`。对这个简单 kernel 来说，如果端到端任务每次都把 32MiB 数据搬进 GPU、算一下、再搬回来，copy 才是更显眼的项。你先看到这个分层，才知道下一步是减少搬运、复用 device memory、改 batch，还是优化 kernel。

## 和本地小模型有什么关系

本地小模型经常慢在这些地方：

| 现象 | 可能瓶颈 | 先看什么证据 |
| --- | --- | --- |
| GPU 利用率低 | CPU tokenizer、数据加载、batch 太小、同步太频繁 | CPU 时间、GPU 时间、队列等待 |
| 显存不够 | capacity-bound | 权重、activation、KV cache、optimizer state、batch、sequence |
| 小 batch 生成慢 | launch/同步/并行度不足 | batch size、tokens/s、kernel 时间 |
| RAG 后更慢 | 检索、序列化、上下文变长 | retrieval time、prompt length、生成 token 数 |
| LoRA 训练 OOM | optimizer state 或 activation 超预算 | trainable params、peak memory、gradient accumulation |

这篇 lab 的作用是让你形成一个习惯：每次慢都先拆层。CPU 数据准备、内存访问顺序、CPU↔GPU 拷贝、kernel 本身、模型显存和评测逻辑要分开看。

## 和已有文章怎么连起来

建议顺序：

1. 先读[数据表示第一课](/computer-science-teaching/2026/03/25/systems-data-representation-bytes-endian.html)，知道 byte、整数宽度和内存中的数据。
2. 再读[系统 cache locality 结课](/computer-science-teaching/2026/03/26/systems-cache-locality-capstone-report.html)，理解为什么 locality 需要实际测量。
3. 读[硬件瓶颈地图](/computer-science-teaching/2026/03/26/hardware-bottleneck-map-cpu-memory-gpu.html)，建立五类瓶颈判断框架。
4. 跑本篇实验，把框架落到 CPU/CUDA 可复跑证据。
5. 再进入 [CUDA thread/block/grid 与 SIMT](/computer-science-teaching/2026/07/03/cuda-thread-index-simt-memory.html) 和 [CUDA reduction、atomic 和 profiling](/computer-science-teaching/2026/04/22/cuda-reduction-atomic-profiling.html)。
6. 最后回到本地小模型和 Agent：看 batch、sequence、RAG、LoRA 和评测如何改变瓶颈位置。

## 常见错误

1. **只看一个数字。** 单次 wall time 可能混合编译、缓存、数据加载、同步和调度抖动。
2. **把小实验当通用 benchmark。** 本篇实验用于认识方向，不用于硬件排名。
3. **没有分离 copy 和 kernel。** CUDA kernel 优化可能真实存在，但端到端时间仍被 host/device transfer 主导。
4. **看到 skipped 就以为失败。** CUDA skipped 只说明当前 shell 找不到可用 `nvcc` 或 GPU 条件不满足；CPU 部分仍然完成了核心学习目标。想跑 CUDA 部分，再按上面的 toolkit-only 步骤补齐工具。
5. **在 WSL 里装 Linux display driver。** WSL 使用 Windows 侧 NVIDIA driver 映射；教学脚本只补 toolkit，不替换 driver。
6. **强行解释 branch 结果。** 分支预测要结合编译器输出、硬件计数器和更严格实验；本篇只建立观察入口。
7. **把第一次 CUDA 时间当结论。** CUDA context 初始化、PTX JIT、页面准备都可能污染第一次计时；本实验显式 warm up，并用 `-arch=native` 降低这个风险。

## 练习

1. 把 `hardware_bottleneck_lab.c` 里的矩阵大小从 `1024` 改成 `512` 和 `2048`，记录 column/row ratio 如何变化。
2. 删除编译参数里的 `-fno-tree-vectorize`，重新运行，观察 stride 和 branch 结果是否变化。解释编译器优化为什么会改变微架构实验。
3. 如果你还没有 CUDA toolkit，先运行 `bash scripts/setup_cuda_runfile_user.sh`，再 `source .tools/cuda-env.sh && bash run_lab.sh`。比较 pageable 和 pinned transfer，只比较同一台机器上的相对关系。
4. 选一个本地 Agent 问答任务，把总耗时拆成 retrieval、prompt construction、model generation、tool call、logging 五段。
5. 对一个 LoRA 训练任务写显存预算表：base weights、adapter、optimizer state、activation、KV cache、batch、sequence。

## 参考资料

- NVIDIA：[CUDA on WSL User Guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
- Ubuntu：[Enable GPU acceleration for Ubuntu on WSL with the NVIDIA CUDA Platform](https://ubuntu.com/wsl/docs/stable/howto/gpu-cuda/)
- NVIDIA：[CUDA Installation Guide for Linux](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html)
- NVIDIA：[CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)
- NVIDIA：[CUDA Runtime API — Event Management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__EVENT.html)
- NVIDIA：[CUDA Runtime API — Memory Management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__MEMORY.html)
- Intel：[Intel® 64 and IA-32 Architectures Optimization Reference Manual](https://cdrdv2-public.intel.com/814198/248966-Optimization-Reference-Manual-V1-049.pdf)

{% endraw %}
