---
layout: post
title: "硬件瓶颈地图：从 CPU cache、内存带宽、PCIe 到 GPU occupancy"
date: 2026-03-26 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把计算机组成原理、操作系统和 CUDA 优化串成一张可执行的瓶颈判断地图。"
tags: [hardware, computer-organization, cache, memory-bandwidth, cuda, gpu, performance]
---
{% raw %}

> **配套实验代码**：先运行系统基础实验 [`assets/labs/computer-systems-os-foundations/`](/labs/#computer-systems-os-foundations)，再对照 CUDA 实验 [`assets/labs/cuda-local-ai-column/`](/labs/#cuda-local-ai-column)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/labs/)。

> **下一步实测**：如果你已经理解这张地图，可以继续读[硬件瓶颈实测第一课：cache、branch、PCIe 和 CUDA timing 怎么一步步看](/computer-science-teaching/2026/03/27/hardware-bottleneck-cache-branch-cuda-transfer-lab.html)，用 `hardware-bottleneck-foundations` 实验把 locality、stride、branch 和 CUDA timing 跑成自己的报告。

学 CUDA、本地小模型和 Agent 优化时，很多人会直接问“这张显卡够不够”“要不要上更大的模型”“怎么把 kernel 写快”。这些问题都合理，但如果没有一张硬件瓶颈地图，很容易把慢归因到错误位置：本来是 Python 数据加载慢，却去改 CUDA block size；本来是 host/device 传输占主导，却只优化 kernel；本来是显存容量卡住，却误以为算力不足。

这篇文章把计算机组成原理、操作系统和 CUDA 编程合成一条学习路线。目标是建立一套可复用的判断流程，用来回答：**当前任务到底卡在计算、内存、通信、同步、容量，还是工程流水线？**

## 学习目标

读完并跑完实验后，你应该能做到：

1. 区分 compute-bound、memory-bound、latency-bound、communication-bound 和 capacity-bound。
2. 用 cache locality 解释为什么同样的循环顺序会产生不同耗时。
3. 解释 CPU 内存层级、GPU memory hierarchy、PCIe/host-device transfer 在一个本地 AI 任务中的位置。
4. 在 CUDA 代码里把 thread/block/grid、warp divergence、atomic、shared memory 和 occupancy 放到同一张判断图里。
5. 面对 RTX 5070 或其他 GPU 时，先问任务证据和瓶颈类型，而不是只问型号。

## 先修知识

建议先读或至少知道这些概念：

- byte、整数宽度、数组连续存储。
- 进程、虚拟内存、文件描述符和线程互斥。
- CUDA 的 host/device、kernel、thread/block/grid。
- 本地小模型任务中的 batch、sequence length、KV cache、LoRA adapter 和 held-out eval。

如果这些还不熟，可以先按栏目里的“计算机系统与操作系统基础”和“CUDA 基础”路线补齐。

## 先跑一个系统证据实验

如果你已经克隆过博客仓库，在 WSL 终端执行：

```bash
cd ~/8rief.github.io
git pull --ff-only
cd assets/labs/computer-systems-os-foundations
bash run_lab.sh
```

这四行分别做了什么：

1. `cd ~/8rief.github.io`：进入你本地的博客仓库。
2. `git pull --ff-only`：只做快进更新，避免把你的本地改动和公开实验混合成分叉历史。
3. `cd assets/labs/computer-systems-os-foundations`：进入系统基础实验目录。
4. `bash run_lab.sh`：用 Bash 运行主脚本，生成 `reports/metrics.json`、`reports/report.md` 和若干 SVG 图。

如果你还没有克隆仓库，先执行：

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/computer-systems-os-foundations
bash run_lab.sh
```

这个实验不会安装软件包，也不会修改你的 home 目录。它会在实验目录下生成 `reports/` 和 `.lab_tmp/`，用于记录本机观察到的数据表示、进程、文件描述符、虚拟内存、线程同步、signal/IPC 和 cache locality 现象。

跑完后重点看两类输出：

```bash
python3 - <<'PY'
import json
from pathlib import Path
m = json.loads(Path('reports/metrics.json').read_text(encoding='utf-8'))
for key in ['cache_column_to_row_ratio', 'thread_controlled_race_actual', 'thread_mutex_actual', 'vm_page_size']:
    print(key, '=', m[key])
PY
```

`cache_column_to_row_ratio` 如果大于 1，说明按列访问二维数组比按行访问慢。原因来自内存连续性和 cache line 利用率，而不是语言语法。CPU 每次从内存层级搬运的是一小段连续数据；按行访问更容易复用刚搬进 cache 的相邻元素，按列访问更容易跨步跳过这段数据。

`thread_controlled_race_actual` 和 `thread_mutex_actual` 用来提醒你：并行不等于自动正确。多个执行单元写同一份状态时，瓶颈可能来自同步、冲突和重试，而非单纯计算速度。

## 一张瓶颈判断图

可以先把任何程序拆成五层：

```text
任务目标
  ↓
算法工作量：到底要做多少数学/搜索/数据处理？
  ↓
数据移动：数据在磁盘、内存、CPU cache、GPU 显存之间怎么流动？
  ↓
并行执行：CPU 线程、GPU warp/block、异步队列如何分配工作？
  ↓
观测证据：计时、带宽、显存、日志、profile、held-out eval 是否支持判断？
```

这张图的关键是顺序：**先确定任务和数据，再谈硬件优化**。如果任务规格都没定，比如输入长度、batch、评价集、最大延迟、显存预算都没有，硬件优化只能靠猜。

## 五类常见瓶颈

| 瓶颈类型 | 典型现象 | 应先收集的证据 | 第一反应不应该是什么 |
| --- | --- | --- | --- |
| compute-bound | 算术指令占主导，数据已经在快存储里 | kernel 时间、FLOP 估算、CPU/GPU 利用率 | 盲目增大 batch 或线程数 |
| memory-bound | 算得不多，但搬数据多 | 有效带宽、cache miss/locality、global memory load/store | 只改算法常数，不看数据布局 |
| latency-bound | 单次等待多，流水线空 | p50/p90/p99、系统调用、网络/磁盘等待 | 用更多线程掩盖无界等待 |
| communication-bound | 设备间或进程间传输占主导 | host↔device bytes、PCIe 传输次数、序列化大小 | 只优化 GPU kernel 内部 |
| capacity-bound | 显存/内存放不下 | peak memory、activation、KV cache、optimizer state | 把 OOM 当成“算力不够” |

同一个项目可能同时包含多种瓶颈。本地小模型最常见的是 capacity-bound 加 communication-bound：模型权重、KV cache、optimizer state、batch 和 sequence length 先决定能不能跑；如果频繁把张量在 CPU 和 GPU 之间搬来搬去，kernel 再快也会被传输吞掉。

## CPU cache 为什么会影响 CUDA 学习

学 CUDA 前补 cache 很有价值，原因有三点：

1. **连续访问优先**。CPU 的 cache line 和 GPU 的 coalesced global memory access 都奖励相邻线程/相邻循环访问连续地址。
2. **层级存储优先**。CPU 有寄存器、L1/L2/L3、DRAM；GPU 有寄存器、shared memory、L1/L2、global memory。名字不同，但“快而小”和“慢而大”的权衡类似。
3. **数据布局优先**。数组的行优先、结构体数组和数组结构体、token batch 的 padding 方式，都会改变实际搬运的数据量。

所以，系统基础实验里的行/列 locality 是理解访存的入口。它对应到 CUDA 里就是：一个 warp 的线程如果访问连续地址，硬件更容易合并内存事务；如果每个线程都跳到很远的位置，吞吐就会下降。

## PCIe 和 host/device 边界为什么重要

CUDA 程序分成 host 端和 device 端。host 端通常负责分配内存、准备输入、启动 kernel、取回结果；device 端负责真正并行执行 kernel。对小任务来说，host/device 拷贝和 kernel launch 开销可能比 kernel 本身更大。

这也是为什么 `vector_add` 只能作为正确性入门，不应该直接拿来宣称 GPU 加速比。一个很小的向量相加，CPU 可能已经足够快；如果你把输入从 CPU 拷到 GPU、启动 kernel、再把输出拷回 CPU，额外开销会掩盖并行收益。只有当任务规模、数据复用和流水线足够合理时，GPU 的吞吐优势才会显现。

在本地小模型里，类似问题也会出现：

- tokenizer 在 CPU 上慢，GPU 可能空等。
- 每轮都重新构造小张量并传到 GPU，传输开销可能过高。
- 生成任务 batch 太小，GPU 并行度不足。
- sequence 太长或 KV cache 太大，显存容量先成为边界。

## CUDA 里的三个优化问题

不要把 CUDA 优化理解成“把 block size 调到某个神秘数字”。更好的起点是三个问题。

### 1. 每个线程做什么？

`threadIdx`、`blockIdx` 和 `blockDim` 决定每个线程处理哪段数据。如果索引公式错了，程序可能越界；如果任务切得太细，launch 和同步开销会变重；如果任务切得太粗，负载不均衡会变重。

N-Queens 的 GPU 版本就是典型例子。搜索树每个分支大小不同，不能只按固定编号平均分给线程。先在 CPU 上用 bitmask DFS 切出足够多的子问题，再让 GPU 动态取任务，才有机会减少空闲线程。

### 2. 数据从哪里读，写到哪里？

全局内存容量大但慢，shared memory 快但小，寄存器最快但会影响 occupancy。reduction 文章里的 atomic 问题说明：多个线程写一个答案时，正确性需要同步；同步位置和粒度决定吞吐。常见做法是先在 block 内做局部归约，再减少跨 block 的全局写冲突。

### 3. warp 是否走同一条路？

GPU 的执行模型适合大量线程执行相似指令。如果同一个 warp 内线程分支严重不同，就会产生 divergence；如果许多线程等待同一个 atomic 或内存位置，也会降低并行效率。搜索、稀疏图、变长文本生成都容易遇到这个问题。

## 把 RTX 5070 放回正确位置

我们的实测会用 RTX 5070，但学习路线不能只为某个型号服务。正确做法是把它看成一个证据平台：

1. 用 `nvidia-smi`、PyTorch CUDA 检查和 `nvcc` 编译确认环境边界。
2. 用小 kernel 验证 host/device、thread/block/grid 和 memory copy 是否正确。
3. 用 N-Queens 或 reduction 观察负载均衡、atomic 和 shared memory 的作用。
4. 用 Qwen/LoRA/RAG 观察显存、batch、sequence、adapter 和 held-out eval 的关系。
5. 再根据你的机器调整模型大小、量化、batch、上下文长度和是否训练 adapter。

如果换成显存更小的 GPU，可能要降低模型大小、使用更激进量化、缩短 sequence 或只跑 CPU-first Agent。换成更大的 GPU，也不代表可以跳过 baseline、held-out eval 和失败分类；硬件变强只扩大可尝试空间，不自动保证任务效果。

## 诊断顺序：慢了先问什么

遇到慢或 OOM，可以按这个顺序排查：

1. **任务是否定义清楚**：输入规模、输出、评价集、延迟/吞吐目标是否明确？
2. **baseline 是否存在**：CPU baseline、简单规则、RAG-only 或小模型 base 是否已经可运行？
3. **数据是否重复搬运**：是否每一步都 CPU↔GPU 来回拷？是否反复读磁盘或重复 tokenize？
4. **容量是否越界**：显存峰值、batch、sequence、optimizer state、KV cache 是否超过预算？
5. **并行是否有效**：线程是否负载均衡？warp divergence 是否严重？atomic 是否集中？
6. **证据是否可复现**：是否记录命令、版本、输入、输出、seed、profile 或 transcript？

只有当前面的答案足够清楚，优化动作才有意义。

## 常见误解

1. **把 GPU 利用率低等同于 GPU 太弱。** 也可能是 CPU 数据准备、I/O、batch 太小或同步太频繁。
2. **把 OOM 等同于算力不足。** OOM 是容量边界，优先看模型大小、activation、KV cache、optimizer state 和 batch。
3. **把单次运行时间当成 benchmark。** 首次运行可能包含编译、缓存、模型加载或磁盘读取；需要区分 warm-up、稳定阶段和数据规模。
4. **把更复杂的 kernel 当成更高级。** 如果瓶颈在传输或数据布局，复杂 kernel 可能只增加调试成本。
5. **把本机实测当成普遍结论。** 本机结果是证据；换 CPU、内存、driver、CUDA toolkit、GPU 和任务规模都可能改变瓶颈。

## 练习

1. 运行系统基础实验，记录 `cache_column_to_row_ratio`。解释为什么这个数字能提醒你关注数据布局。
2. 在 CUDA vector add 实验里，把输入规模调小和调大，分别解释为什么小规模不适合谈加速比。
3. 在 reduction 实验里比较 naive atomic 和分层归约，说明“正确写同一个答案”和“高吞吐写同一个答案”的区别。
4. 对一个本地小模型任务写出显存预算表：权重、activation、KV cache、optimizer state、LoRA adapter、batch 和 sequence length。
5. 如果 Agent 响应慢，先列出 CPU 检索、模型生成、工具调用、日志写入、网络/磁盘等待五个候选瓶颈，再设计最小计时点。

## 参考资料

- NVIDIA：[CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)
- NVIDIA：[CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)
- Intel：[Intel® 64 and IA-32 Architectures Optimization Reference Manual](https://www.intel.com/content/www/us/en/content-details/671488/intel-64-and-ia-32-architectures-optimization-reference-manual-volume-1.html)

{% endraw %}
