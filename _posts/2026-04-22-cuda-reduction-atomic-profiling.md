---
layout: post
title: "CUDA reduction、atomic 和 profiling：多个线程写同一个答案怎么办"
date: 2026-04-22 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用分层归约和 readiness 报告解释竞争、atomic、同步和为什么没有本地实测不能报告加速。"
tags: [cuda, reduction, atomic, profiling, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/cuda-local-ai-column/README.md`](/assets/labs/cuda-local-ai-column/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：CUDA / reduction / atomic / profiling
> 本文 lab 首次发布时验证了 8 个数的分层 reduction 过程并生成 `block_reduction.cu`；当时 `nvcc` 缺失，因此不报告 GPU 加速。后续已在[硬件瓶颈实测第一课](/computer-science-teaching/2026/03/27/hardware-bottleneck-cache-branch-cuda-transfer-lab.html)补齐用户态 toolkit；但 reduction 性能仍需要单独用 CUDA event/profiler 验收，不能由“工具链可用”自动推出。

vector add 每个线程写不同位置，几乎没有协作。很多真实任务不同：求和、直方图、计数、N-Queens 解数量都要求多个线程贡献到同一个结果。这时要处理写冲突。

## 学习目标

1. 区分独立写、atomic 写和分层 reduction。
2. 理解为什么 atomic 正确但可能慢。
3. 理解 shared memory reduction 为什么需要同步。
4. 说明没有 CUDA event 或 profiler 时不能随意报告 kernel 时间。

## 需求：把很多局部结果合成一个答案

假设有 8 个数：

```text
[1,2,3,4,5,6,7,8]
```

串行求和很简单，但并行求和要决定谁和谁先加，结果写到哪里。lab 的 reduction steps 为：

```text
stride=4 -> [6,8,10,12]
stride=2 -> [16,20]
stride=1 -> [36]
```

这就是树形归约：先把距离 4 的元素相加，再把距离 2 的部分和相加，最后得到总和 36。

## 核心模型

```text
每线程产生局部值
-> block 内 shared memory 合并
-> block 结果写入 partial array
-> host 或第二个 kernel 合并 partial
```

atomic 的模型更直接：每个线程都对同一个全局计数器做原子加。但如果所有线程都抢一个地址，硬件必须串行化这些冲突，吞吐会下降。

## 为什么这样做

分层 reduction 用额外的局部合并步骤减少全局竞争。先在 block 内用 shared memory 汇总，再把少量 partial 写回 global memory，可以降低 atomic 热点。

N-Queens 计数也有同类问题：每个子问题产生局部解数，最终要合成全局答案。高性能实现通常避免让所有线程频繁写同一个全局变量。

## profiling 边界

CUDA kernel launch 默认异步。用 CPU 的 wall clock 包住 launch，可能测到的是发射开销，而不是 GPU 执行时间。后续真正做性能实验时应使用：

```text
CUDA event timing
cudaDeviceSynchronize boundary
Nsight Systems / Nsight Compute
problem-size sweep
CPU baseline
```

当前本机 `nvcc` 缺失，lab 只生成 CUDA 源码和 CPU/逻辑报告。因此本文不报告任何“GPU 加速倍数”。

## shared memory reduction 的同步点

教学版 block reduction 的核心状态变化可以写成：

```cpp
extern __shared__ float partial[];
unsigned int tid = threadIdx.x;
unsigned int i = blockIdx.x * blockDim.x + tid;
partial[tid] = (i < n) ? input[i] : 0.0f;
__syncthreads();

for (unsigned int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (tid < stride) partial[tid] += partial[tid + stride];
    __syncthreads();
}

if (tid == 0) block_sums[blockIdx.x] = partial[0];
```

第一次同步保证每个线程已写入自己的局部值。循环中的同步保证当前 stride 的所有加法结束后，下一轮才读取这些结果。`__syncthreads()` 是 block 级屏障，不能让不同 block 互相等待；因此每个 block 先写一个 `block_sums`，再由第二个 kernel 或 host 完成最终合并。

边界线程写 `0.0f` 是加法单位元。它让最后一个不满的 block 也能参与同一套 reduction，而不会读取数组外数据。

## 复跑结果与正确性检查

运行并读取报告：

```bash
./run_lab.sh
grep -A8 '^## Reduction' reports/cuda_foundations_report.md
```

预期输出的最后一轮是：

```text
stride 4 -> [6, 8, 10, 12]
stride 2 -> [16, 20]
stride 1 -> [36]
```

`36` 应等于 CPU 的 `sum([1,2,3,4,5,6,7,8])`。真实浮点输入还要定义误差阈值，因为并行加法改变了求和顺序；浮点加法不满足严格结合律。整数计数则应与 CPU oracle 完全一致，并检查是否可能溢出。

## 性能实验需要哪些对照

至少比较以下三种实现：

```text
CPU serial sum
GPU global atomic sum
GPU block reduction + final merge
```

固定数据类型、输入分布、总元素数和正确性标准；分别报告端到端时间和 kernel 时间。再做输入规模 sweep，观察 launch overhead、内存带宽和竞争分别在哪些区间主导。Nsight 证据用于解释现象，不能用“shared memory 通常更快”代替本机测量。

## RTX 5070 落地与迁移边界

不同 GPU 的 atomic 吞吐、shared memory 带宽和调度能力不同。5070 上测得的最优 block size 或 reduction 版本不能直接推广到 A100/H100；但“先减少竞争，再测量瓶颈”的原则不变。

## 常见错误

1. **所有线程直接 atomic 到一个全局变量。** 正确但可能非常慢。
2. **shared memory reduction 忘记同步。** 读到的可能是其他线程尚未写完的数据。
3. **只测一个规模。** 小规模可能被 launch 开销支配，大规模才暴露带宽或计算瓶颈。
4. **没有 profiler 却解释底层瓶颈。** 没有证据时只能说是假设。

## 练习

把 16 个数的 reduction steps 写出来。思考如果 block 内先求和，再对每个 block 的 partial 做一次 atomic，会比所有线程 atomic 到同一个全局变量少多少竞争。

## 参考资料

- NVIDIA 文档：[CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html)
- NVIDIA 文档：[CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)

{% endraw %}
