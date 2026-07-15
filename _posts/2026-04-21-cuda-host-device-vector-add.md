---
layout: post
title: "CUDA 第一个 kernel：vector add 背后的 host/device 边界"
date: 2026-04-21 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 vector add 建立 CUDA 程序最小闭环：CPU 准备、GPU 执行、显存复制、正确性检查和 nvcc readiness。"
tags: [cuda, gpu, vector-add, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/cuda-local-ai-column/README.md`](/assets/labs/cuda-local-ai-column/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：CUDA / host-device model / vector add
> 本文 lab 首次发布时验证了 CPU vector add 正确、`vector_add.cu` 已生成；当时 shell 因 `nvcc not found` 跳过 CUDA C++ 编译。后续已在[硬件瓶颈实测第一课](/computer-science-teaching/2026/03/27/hardware-bottleneck-cache-branch-cuda-transfer-lab.html)补齐用户态 toolkit 并跑出 `CUDA_STATUS=ok`；本文仍把“没有 `nvcc` 时不能声称 CUDA C++ 实测”作为 readiness 边界。

学 CUDA 的第一步不应该是追求复杂优化，而是把 CPU 和 GPU 的职责边界讲清楚。GPU 不会自动接管一段 C++ 循环；程序必须显式申请 device memory、把数据从 host 复制到 device、发起 kernel，再把结果复制回来。

## 学习目标

1. 解释 host、device、global memory 和 kernel launch 的关系。
2. 读懂 `blockIdx.x * blockDim.x + threadIdx.x` 为什么是全局索引。
3. 区分正确性实验和性能实验。
4. 理解为什么没有 `nvcc` 时不能声称完成 CUDA C++ 实测。

## 需求：把一个独立循环交给 GPU

vector add 的业务含义很简单：给定 `a[i]` 和 `b[i]`，计算 `c[i]=a[i]+b[i]`。它适合做第一课，因为每个元素彼此独立，不需要锁、通信或复杂调度。这样的循环能直接暴露 CUDA 的基本执行边界。

## 核心模型

```text
CPU host: allocate and initialize a,b
    -> cudaMalloc device buffers
    -> cudaMemcpy host to device
    -> launch vector_add<<<grid, block>>>
GPU device: each thread computes one c[i]
    -> cudaMemcpy device to host
CPU host: check c[i] == a[i] + b[i]
```

这个模型解释了为什么小数组不一定适合 GPU：即使 kernel 很快，内存复制和 launch 开销也可能超过计算本身。

## 为什么需要先划清 host/device 边界

CUDA 程序同时管理两个执行位置和至少两个内存位置。普通 `new`、`malloc` 或 `std::vector` 默认得到 host memory；kernel 访问的输入通常要先进入 device memory。只看 kernel 的一行加法，会遗漏分配、复制、同步、错误检查和释放，程序也就缺少完整的正确性链路。

把一次计算写成状态表更容易排查问题：

| 阶段 | 数据位置 | 谁执行 | 必须检查什么 |
| --- | --- | --- | --- |
| 初始化 | host | CPU | 输入长度和值 |
| `cudaMalloc` | device | CUDA runtime | 返回状态、字节数 |
| H2D copy | host → device | CUDA runtime | 方向和长度 |
| kernel | device | GPU | grid、block、边界 |
| D2H copy | device → host | CUDA runtime | 同步后的结果 |
| verify/free | host/device | CPU/runtime | 误差、错误状态、释放 |

其中任何一步失败，都不应继续输出“计算成功”。后续真实编译时，应在每个 runtime API 后检查 `cudaError_t`，kernel launch 后同时检查 launch error 和同步 error。

## 最小 kernel

lab 生成的 `vector_add.cu` 核心是：

```cpp
__global__ void vector_add(const float* a, const float* b, float* c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}
```

`if (i < n)` 是边界检查。grid 通常会向上取整，最后一个 block 可能有部分线程的索引超过数组长度。没有这行判断，程序就可能越界写。

## 本地实验结果

运行栏目 lab：

```bash
./run_lab.sh
```

关键结果：

```text
cuda_foundations_ok True skipped
```

含义是：CPU vector add 正确；CUDA 源码已经生成；但本机当前缺少 `nvcc`，所以 CUDA C++ 编译被标记为 `skipped`。这是诚实的验收边界，不是失败。后续安装 CUDA toolkit 后，同一个 lab 应从 `skipped` 变成 `compiled` 并运行 `vector_add_ok`。

报告还保留了 CPU 参考结果：`n=16`，最后一个元素为 `45.0`，逐元素比较通过。这个 CPU 结果是 oracle；GPU 版本必须产生同一组值，性能比较只能在正确性通过后开始。

安装 toolkit 后，可以按下面的最小顺序验证：

```bash
nvcc --version
nvcc -O2 -arch=sm_120 src/vector_add.cu -o /tmp/vector_add
/tmp/vector_add
```

预期先看到编译器版本，再看到程序自己的正确性标记。若 `sm_120` 不受当前 toolkit 支持，应先核对该 toolkit 的 architecture support，选择它实际支持且与设备兼容的目标；不要随意复制其他显卡的 `-arch`。

## 从正确性实验进入性能实验

性能实验至少要拆开三种时间：

```text
H2D copy time
kernel execution time
D2H copy time
```

端到端需求关心三者总和；kernel 优化关心中间一项。应使用 CUDA events 测 device 时间，并在计时前 warm up，在多个输入规模上重复运行，报告中位数或分位数。CPU baseline 要执行相同的向量加法和相同精度的校验。只有这样，才能回答“GPU 从多大规模开始值得使用”。

如果只测一个很小的 `n`，结论往往由 launch 和复制开销决定；如果只报告 kernel 时间，又会隐藏数据搬运成本。两种口径都可以保留，但列名和解释必须明确。

本栏目后面的[硬件瓶颈实测第一课](/computer-science-teaching/2026/03/27/hardware-bottleneck-cache-branch-cuda-transfer-lab.html)会把这件事拆成可运行实验：CPU 侧先看 cache/stride/branch，CUDA 侧再分别记录 pageable/pinned copy 和 kernel event timing。

## 为什么这样做

先写 vector add 的价值不在算术，而在程序结构。后续矩阵乘法、reduction、N-Queens 子问题搜索都要重复这条链路：host 准备任务，device 并行执行，host 验证结果。把这条链路跑通后，性能优化才有意义。

## RTX 5070 落地与迁移边界

本机 RTX 5070 的 compute capability 是 12.0。真正编译时应使用适合当前架构的目标，例如 `sm_120`。如果换成旧 GPU，编译目标和可用特性会不同；如果换成 24GB 或 40GB GPU，vector add 的概念不变，只是可测试规模和吞吐上限改变。

## 常见错误

1. **只写 kernel，不检查结果。** 第一个实验必须先验证正确性。
2. **把 CPU timer 当成 GPU kernel 时间。** CUDA launch 是异步的，后续需要 CUDA event 或同步边界。
3. **没有 nvcc 却报告 CUDA 实测。** 当前只能报告 readiness gap 和源码生成。
4. **忘记边界检查。** grid 向上取整后，越界线程是常态。

## 练习

把 `n=16` 改成 `n=20`，手算需要几个 `blockDim=8` 的 block。答案是 3 个 block，共 24 个线程，其中 4 个线程应被边界检查挡住。

## 参考资料

- NVIDIA 文档：[CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html)
- NVIDIA 文档：[CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)

{% endraw %}
