---
layout: post
title: "CUDA thread/block、SIMT 和访存：为什么索引和地址决定性能"
date: 2026-07-03 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 thread index map 和 stride 地址实验解释 SIMT、活跃线程、连续访存和迁移到不同GPU的边界。"
tags: [cuda, simt, memory, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/cuda-local-ai-column/README.md`](/assets/labs/cuda-local-ai-column/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：CUDA / thread index / SIMT / memory
> 本文 lab 已验证：`n=20`、`blockDim=8` 时需要 24 个线程，其中 20 个 active；stride 地址表已生成。

GPU 编程首先要回答两个问题：每个线程处理哪个元素，以及它访问哪个地址。索引错了，程序不正确；地址模式差，程序可能很慢。

## 学习目标

1. 用 block、thread 和 global index 解释任务划分。
2. 理解 SIMT 是多个线程执行同一指令流，而不是一个巨大的单线程。
3. 解释连续访存为什么通常比 stride 访存更适合 GPU。
4. 区分线程组织的通用原理和具体硬件规模。

## 需求：覆盖任意长度数组

数组长度很少刚好等于 block 大小的整数倍。CUDA kernel 需要用全局索引覆盖所有元素，同时让多出来的线程安全退出。

lab 生成的 thread map 片段如下：

```text
block 0, thread 0 -> global_i 0  active True
...
block 2, thread 3 -> global_i 19 active True
block 2, thread 4 -> global_i 20 active False
```

这说明最后一个 block 里有 4 个 inactive 线程，它们来自向上取整，应该由边界判断安全退出。

## 核心模型

```text
grid = blocks
block = threads that can cooperate
thread = one logical lane of work
global_i = blockIdx.x * blockDim.x + threadIdx.x
```

SIMT 的直觉是：一组线程执行同一段 kernel 代码，但每个线程用自己的索引和数据。分支会让同一组线程走不同路径，访存会让同一组线程请求不同地址。

## 访存为什么重要

lab 给出 8 个线程在不同 stride 下访问 float 数组的地址：

```text
stride=1 -> [0,4,8,12,16,20,24,28]
stride=2 -> [0,8,16,24,32,40,48,56]
stride=4 -> [0,16,32,48,64,80,96,112]
```

连续访问更容易合并成高效内存事务。stride 越大，同一组线程访问越分散，显存带宽利用率越可能下降。真实 GPU 的合并规则和缓存层级更复杂，但第一性原理很简单：算术单元等数据时，吞吐就会掉。

## 如何复现实验并读输出

在栏目实验目录运行：

```bash
./run_lab.sh
sed -n '1,80p' reports/cuda_foundations_report.md
```

稳定摘要包含：

```text
cuda_foundations_ok True skipped
```

第一个值表示 CPU vector add oracle 通过，`skipped` 表示本机尚无 `nvcc`。随后查看 thread map，应能数到 24 行线程记录，其中 20 行 `active=True`、4 行 `active=False`。计算过程是：

```text
blocks = ceil(20 / 8) = 3
launched_threads = 3 * 8 = 24
inactive_threads = 24 - 20 = 4
```

这个输出把 launch shape 和数据边界对应起来。若 active 数量不是 20，应先检查向上取整和 `i < n`，不要从性能参数入手。

## 分支与 SIMT 的状态变化

同一 warp 中的线程遇到数据相关分支时，可能需要分别执行不同路径。例如：

```cpp
if (x[i] >= 0.0f) {
    y[i] = sqrtf(x[i]);
} else {
    y[i] = 0.0f;
}
```

若同一 warp 的输入正负混合，活跃 lane 会随分支路径改变。分支不必然慢；关键在于同组线程是否经常走不同路径，以及每条路径工作量多大。优化时先用 profiler 观察 branch efficiency 或 warp state，再决定是否重排数据或改写算法。

访存也要从“线程编号到字节地址”的映射检查。本文的 float 元素宽度为 4 字节，因此 stride 1 的地址差为 4，stride 8 的地址差为 32。报告展示的是地址模式模型，不等同于某一代 GPU 的实测事务数量。

## 为什么这样做

后续小模型训练里的矩阵乘法、attention 和 embedding 查表同样受访存模式影响。CUDA 基础让我们能解释某些 shape、batch、sequence length 为什么导致吞吐下降或显存不足，而无需把所有深度学习算子都手写一遍。

## RTX 5070 落地与迁移边界

RTX 5070、A100、H100 或更小的消费级 GPU 都使用 thread/block/grid 的同一编程模型。差异在于 SM 数量、显存带宽、cache、支持的指令和可承载规模。文章中的索引公式不变，但最佳 block size、occupancy 和实际吞吐需要针对硬件测量。

## 常见错误

1. **把 block 当成越大越好。** block 太大可能增加寄存器和 shared memory 压力。
2. **忽略 inactive 线程。** 最后一个 block 的越界线程必须显式挡住。
3. **只看算术复杂度。** GPU 程序经常卡在访存和同步。
4. **把 SIMT 当成 CPU 多线程。** SIMT 的分支和同步代价有自己的规则。

## 练习

用 `n=1000`、`blockDim=256` 计算需要多少 block，总线程数是多少，inactive 线程数是多少。再思考如果每个线程访问 `x[i*4]`，地址模式和 `x[i]` 有什么不同。

## 参考资料

- NVIDIA 文档：[CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html)
- NVIDIA 文档：[CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)

{% endraw %}
