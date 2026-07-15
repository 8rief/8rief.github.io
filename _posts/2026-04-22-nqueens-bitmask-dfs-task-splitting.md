---
layout: post
title: "N-Queens 从 bitmask DFS 到 GPU 子问题：为什么搜索要先切任务"
date: 2026-04-22 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用小规模 N-Queens 计数和预放行子问题解释状态压缩、对称前的搜索树和 GPU 任务粒度。"
tags: [cuda, n-queens, bitmask, search, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/cuda-local-ai-column/README.md`](/assets/labs/cuda-local-ai-column/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：CUDA / N-Queens / bitmask DFS / task splitting
> 本文 lab 已验证：N=4..8 的解数为 2、10、4、40、92；N=8 预放 3 行得到 140 个子问题。

N-Queens 是一棵分支不均匀的搜索树。单个位置的合法性判断很短，但不同前缀会展开出差异很大的后续工作量，这构成了 GPU 加速的主要难点。

## 学习目标

1. 用 bitmask 表示列和对角线约束。
2. 解释 DFS 为什么能计数 N-Queens 解。
3. 理解“预放若干行”为什么能生成 GPU 子问题。
4. 区分教学版任务切分和真实高性能源码中的更多优化。

## 需求：把不规则搜索变成许多可分配任务

CPU 递归 DFS 从空棋盘开始，每次选择下一行的合法列。bitmask 状态为：

```text
cur   = 已占用列
left  = 左斜线攻击到下一行的列
right = 右斜线攻击到下一行的列
valid = full & ~(cur | left | right)
```

当 `cur == full`，表示每一列都已经放了一个皇后，也就是找到一个完整解。

## 为什么需要 bitmask 状态

普通棋盘数组需要逐格检查列和两条对角线。bitmask 把“哪些列被占用”压成整数中的位，使合法位置可以用几个位运算一次得到。每轮取出最低有效位：

```text
bit   = valid & -valid
valid = valid ^ bit
```

`bit` 代表当前选择的列，第二行从候选集合中移除它。进入下一行时，三类约束更新为：

```text
next_cur   = cur | bit
next_left  = (left | bit) << 1
next_right = (right | bit) >> 1
```

左移和右移对应两条对角线在下一行攻击位置的变化。所有状态都通过函数参数传入，因此每个 DFS 分支拥有独立状态，回溯时无需恢复共享棋盘。

用 `N=4` 时，`full=0b1111`。若第一行选择最左一列 `bit=0b0001`，下一行的占用与对角线 mask 会共同排除受攻击列。把二进制值打印出来，比只画棋盘更容易核对位移方向。

## 小规模正确性

lab 输出：

```text
N=4 -> 2
N=5 -> 10
N=6 -> 4
N=7 -> 40
N=8 -> 92
```

这些小规模计数是后续 CUDA 版本的正确性基线。没有小规模基线，GPU 代码即使跑得很快也无法信任。

## 为什么要预放行

如果直接让一个 GPU 线程从根节点开始 DFS，任务数量太少，而且分支极不均匀。更合理的方法是先在 CPU 或 host 侧展开前几行，把每个前缀状态作为子问题：

```text
root
 -> preplace row 0
 -> preplace row 1
 -> preplace row 2
 -> many independent subproblems
```

本次 lab 中，N=8 预放 3 行得到 140 个子问题。每个子问题可以交给一个线程或一个工作单元继续搜索。

复跑实验并检查两个关键事实：

```bash
./run_lab.sh
grep -A8 '^## Known small counts' reports/nqueens_bridge_report.md
grep -A6 '^## Subproblem split' reports/nqueens_bridge_report.md
```

预期看到 `N=8 -> 92` 和 `140 subproblems`。前者验证 DFS 计数，后者只描述预放 3 行后的任务数量。140 不是解数；每个子问题仍可能产生 0 个、1 个或多个完整解。

## 子问题接口要保存什么

一个可独立执行的子问题至少需要保存当前行数和三类 mask：

```text
Task { row, cur, left, right }
```

host 生成任务时要保证状态没有截断，device 继续 DFS 时使用同一位宽和相同终止条件。若 `N` 接近整数位宽上限，`full=(1<<N)-1` 可能发生移位未定义或溢出；实现应选择明确的无符号位宽并限制输入范围。

任务粒度还影响传输和调度：预放较浅会得到少量大任务，较深会得到大量小任务。实验应记录预放深度、任务数、每任务工作量分布、host 展开时间和 device 搜索时间，才能选择合理切分点。

## 为什么这样做

GPU 擅长大量任务并行。预放行把一棵搜索树切成一批任务，让 GPU 有足够并行度。预放太少，任务数不够；预放太多，host 生成任务成本上升，而且每个任务太小。最佳行数要测量，不应固定迷信某个值。

## RTX 5070 落地与迁移边界

5070 可以用教学规模 N=12..16 做 correctness/timing；更大的 N 会迅速变成长时间搜索。换成更强 GPU 或多 GPU，只是扩大可搜索规模，不改变“先切子问题、再动态调度”的需求。

## 常见错误

1. **只看最终 N 很大。** 教学和调试应从 N=4..8 的已知答案开始。
2. **把预放行数当常数。** 它是任务粒度参数，要根据 N 和硬件测量。
3. **忽略子问题耗时差异。** 同样预放 3 行，不同前缀后续搜索量可能差很多。
4. **把 bitmask 当技巧。** 它是状态表示，直接影响搜索速度和 GPU 栈设计。

## 练习

手算 N=4 的第一行放在第 1 列后，下一行哪些列被 `cur|left|right` 禁止。再和 bitmask lab 的 `valid` 计算对照。

## 参考资料

- 参考项目：[ygch/n_queens](https://github.com/ygch/n_queens)
- Stanford Bit Twiddling Hacks：[Bit hacks](https://graphics.stanford.edu/~seander/bithacks.html)

{% endraw %}
