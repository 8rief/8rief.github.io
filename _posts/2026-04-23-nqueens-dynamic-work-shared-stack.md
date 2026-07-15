---
layout: post
title: "N-Queens GPU 桥梁：dynamic work fetching 和 shared-memory stack 为什么出现"
date: 2026-04-23 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从负载不均衡、显式栈和源码边界解释真实 CUDA N-Queens 实现为什么使用 atomic 和 shared memory。"
tags: [cuda, n-queens, shared-memory, atomic, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/cuda-local-ai-column/README.md`](/assets/labs/cuda-local-ai-column/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：CUDA / N-Queens / dynamic work / shared memory stack
> 本文 lab 已验证：N=8 预放 3 行的静态 round-robin 负载不均衡为 4，动态贪心模拟不均衡为 0。该数字是教学估计，不是 GPU benchmark。

真实 N-Queens GPU 代码比 vector add 难，因为每个子问题耗时不同。静态分配任务时，某些线程可能很快结束，另一些线程仍在搜索深层分支。GPU 利用率就会下降。

## 学习目标

1. 解释为什么不规则搜索需要动态取任务。
2. 理解 `atomicAdd` 在 work queue 中的角色。
3. 解释为什么 DFS 递归会被改成显式栈。
4. 理解 shared memory stack 的动机和边界。

## 需求：减少负载不均衡

lab 用估计工作量模拟 N=8 的 140 个子问题。静态 round-robin 和动态贪心调度得到：

```text
static round-robin imbalance = 4
dynamic greedy imbalance     = 0
```

这不是性能结论，只说明同一批任务若耗时不同，动态分配有机会让 worker 负载更平衡。

## dynamic work fetching

真实 CUDA 实现可以用一个全局计数器表示“下一个未处理任务”。线程完成当前任务后：

```text
tid = atomicAdd(global_counter, 1)
process task[tid]
```

`atomicAdd` 保证每个线程拿到不同任务编号。这样快线程不会空等，而是继续领取新任务。

## 为什么需要动态任务边界

静态 round-robin 只保证任务数量接近，不能保证工作量接近。假设两个 worker 依次收到：

```text
tasks = [10, 1, 1, 1, 10, 1, 1, 1]
```

若按任务下标轮流分配，worker 0 得到 `10+1+10+1=22`，worker 1 得到 `1+1+1+1=4`。总完成时间由 22 决定。动态队列让空闲 worker 继续取下一个任务，通常能缩小尾部等待，但会引入 atomic、队列访问和调度开销。

因此动态取任务适合“单任务成本差异明显、任务数量足够多”的场景。若所有任务成本几乎相同，静态分配更简单，也可能更快。

一个安全的领取循环还要检查队列边界：

```cpp
while (true) {
    unsigned int task_id = atomicAdd(next_task, 1U);
    if (task_id >= task_count) break;
    process(tasks[task_id]);
}
```

`atomicAdd` 只分配唯一编号，不保护 `process` 内部的其他共享状态。解计数、错误标记和输出缓冲区仍要分别设计同步方式。

## 为什么需要显式栈

DFS 天然写成递归，但 GPU kernel 中递归会带来栈和调用开销，也不利于控制局部状态布局。教学版可以把 DFS 状态写成数组栈：

```text
push(cur, left, right, valid)
while stack not empty:
    pop or update top
    choose lowbit
    push next state
```

真实高性能版本会进一步把频繁访问的栈放到 shared memory，减少 global memory 访问。

显式栈的每一层需要保存能恢复 DFS 的完整状态，例如：

```text
Frame { cur, left, right, remaining_valid }
```

`remaining_valid` 记录这一层尚未尝试的列。循环先从栈顶取一个 `lowbit`，更新当前层剩余候选，再压入下一行状态；下一行没有候选时弹栈。这个过程与递归调用一一对应，因此可以先在 CPU 上写显式栈版，与递归版对拍，再迁移到 kernel。

## shared memory 的取舍

shared memory 延迟低，但容量有限，还要考虑 bank conflict。把每个线程的 DFS stack 放进 shared memory，可以加速频繁 push/pop；但如果布局不当，多个线程访问同一个 bank，也会冲突。

`ygch/n_queens` 这类项目值得读，因为源码展示了搜索树、任务调度、栈状态与 GPU 存储层级如何共同约束实现。

## 如何复跑并解释调度报告

```bash
./run_lab.sh
cat reports/nqueens_bridge_report.md
```

本次固定输入的摘要是：

```text
subproblems = 140
static worker loads  = [263, 259, 259, 263]
dynamic worker loads = [261, 261, 261, 261]
imbalance             = 4 -> 0
```

这些 load 来自教学用工作量估计，动态结果使用能预知任务成本的贪心模拟。真实 GPU 调度无法提前知道每个搜索子树的精确成本，所以 `0` 不能解释为实际执行会完全均衡。报告只证明：当前任务集合存在可比较的调度模型，且动态分配的动机可以被量化。

真实验证应同时保留小 N 解数、每个 block/worker 处理任务数、总搜索节点数、队列 atomic 次数和 kernel 时间。若动态版更慢，就要判断开销来自 atomic 热点、任务太小、栈访问或 occupancy 下降，而不是直接增加更多机制。

## 从 CPU oracle 到 GPU 验收

推荐按三层验收：

1. CPU 递归版与已知 `N=4..8` 解数一致。
2. CPU 显式栈版逐个 N 与递归版一致。
3. GPU 动态队列版逐个 N 与 CPU oracle 一致，再比较性能。

这种顺序让状态表示、栈转换和并行调度各自有独立的错误定位边界。只看最终 GPU 总数时，一旦错误很难判断来自哪一层。

## RTX 5070 落地与迁移边界

本机实际编译时不能照抄 4090 的 `sm_89` 参数，应按 compute capability 12.0 使用合适目标。更强 GPU 可能让更大 N 可行，但 dynamic work、显式栈和 shared memory 布局仍需 profiling 验证。

## 常见错误

1. **把 atomic 当成免费调度器。** atomic 自身也有竞争，只是比静态空等更适合某些不规则任务。
2. **把 shared memory 当万能缓存。** 容量、bank conflict 和 occupancy 都可能成为新瓶颈。
3. **跳过 CPU correctness。** GPU 搜索必须先和小 N 已知解数对齐。
4. **直接复制源码参数。** 架构、block size、预放行数都要按硬件和 N 重新验证。

## 练习

设计一个任务列表 `[10,1,1,1,10,1,1,1]`，比较 2 个 worker 的静态 round-robin 和“谁空谁取下一个”的动态调度负载。

## 参考资料

- 参考项目：[ygch/n_queens](https://github.com/ygch/n_queens)
- NVIDIA 文档：[CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html)

{% endraw %}
