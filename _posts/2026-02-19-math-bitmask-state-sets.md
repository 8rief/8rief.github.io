---
layout: post
title: "bitmask 状态集合：为什么一个整数能表示一组候选"
date: 2026-02-19 09:00:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "从有限集合和二进制位出发，解释 mask、补集、lowbit 和 N-Queens 搜索状态，为后续 CUDA 搜索优化做数学准备。"
tags: [math, bitmask, state-space, n-queens, teaching]
---
{% raw %}
> 主题：数学基础 / 位集合 / 搜索状态
> 本文 lab 已验证：`N=5` 时 `full_mask=11111`，放置两行后下一行合法候选为 `00001`，lowbit 对应 column `0`。

后续读 N-Queens、状态压缩动态规划和 CUDA 搜索代码时，经常会看到 `mask`、`valid_pos`、`p = valid & -valid` 这类表达式。它们看起来像位运算技巧，本质上是在用一个整数表示有限集合：第 `i` 位为 1，表示集合里包含元素 `i`。

这个表示法的价值在于把“哪些列已经被占用”“哪些位置仍可选择”“取出一个候选”等集合操作变成少数机器指令。对搜索问题来说，除了节省内存，它还会直接影响 CPU 和 GPU 上的执行效率。

## 为什么需要位集合表示

搜索和动态规划经常要反复保存“当前还剩哪些候选”。如果每次都用数组或布尔表扫描，状态复制、合法性检查和候选枚举都会变成显式循环。规模小的时候这不明显；当状态被放进 DFS、DP 表或 GPU 线程局部变量里时，表示方式会直接影响每一步的成本。

bitmask 的作用是把有限集合压进一个整数。这样，集合并、交、补、删除最低候选都能用固定几条位运算表达。代码变短只是表面结果，真正的价值在于状态边界更清楚：一个 mask 就是一组候选，一个转移就是一次集合变换。

因此，学习 bitmask 时要同时看数学含义和机器执行含义。数学上它是子集表示；工程上它减少内存访问、分支和状态复制。

## 问题从哪里来

以 N-Queens 为例，每一行要选一列放皇后。若用数组保存棋盘，每次判断新位置是否合法，都要检查同列和两条对角线。更紧凑的做法是维护三个集合：已占用列、被左斜线攻击的列、被右斜线攻击的列。下一行的合法集合就是全集减去这些被禁止的位置。

当 `N` 不大时，一个机器整数的二进制位足以表示这些集合。于是集合运算可以写成：

```text
blocked = cur | left | right
valid   = full & ~blocked
```

这里的 `|` 是集合并，`~` 是补集，`&` 是交集过滤。

## 正式定义

设全集为 `U={0,1,...,N-1}`。一个整数 `m` 表示集合 `S(m)={i in U : m 的第 i 位为 1}`。例如 `N=5` 时，`m=01010₂` 表示集合 `{1,3}`。

几个基本操作对应如下：

| 位运算 | 集合意义 |
| --- | --- |
| `a | b` | 并集 |
| `a & b` | 交集 |
| `full & ~a` | 在全集内取补集 |
| `a ^ b` | 对称差，或翻转不同位 |
| `x & -x` | 取最低的 1 位，对应取出一个候选元素 |
| `x -= lowbit` | 从候选集合删除这个元素 |

`full=(1<<N)-1` 的作用是把补集限制在前 `N` 位。没有这个限制，`~a` 会在整数表示中产生无限多高位 1，不再对应原来的有限集合。

## 直观模型

![bitmask 表示有限状态集合](/assets/diagrams/math-bitmask-state-sets.svg)

把二进制位从右到左看成列编号。第 0 列对应最低位，第 4 列对应第五位。一个 1 表示该列属于当前集合；一个 0 表示不属于。

## 怎么算

实验使用 `N=5`。全集为：

```text
full = 11111
```

假设前两行已经把皇后放在第 1 列和第 3 列。脚本逐行更新三个 mask：

```python
cur = cur | bit
left = (left | bit) << 1
right = (right | bit) >> 1
valid = full & ~(cur | left | right)
```

本次 lab 输出：

```text
full_mask=11111
valid_after_two_rows=00001
choices=0
```

报告中的中间状态为：

```text
after row 1: cur=00010, left=00100, right=00001, valid=11000
after row 2: cur=01010, left=11000, right=00100, valid=00001
```

最后的 `valid=00001` 表示下一行只有第 0 列可选。取出这个候选：

```python
lowbit = valid & -valid
column = lowbit.bit_length() - 1
```

得到 `lowbit=00001` 和 `column=0`。

## 为什么 `x & -x` 能取最低 1 位

以 `x=10100₂` 为例，二进制补码里的 `-x` 会把最低 1 位及其右侧结构变成只保留这个最低 1 位可相交的形式。于是：

```text
x      = 10100
-x     = 01100  （只看相关低位直觉）
x & -x = 00100
```

更安全的理解方式是：最低 1 位右侧全是 0，取负时这些低位保持能让最低 1 位被单独分离；更高位即使变化，与原数相与后也不会留下比最低 1 位更低的 1。

## 有什么用

1. **N-Queens 搜索。** `cur`、`left`、`right` 三个 mask 能快速给出下一行合法位置。
2. **状态压缩 DP。** 一个子集状态可以直接作为数组下标。
3. **集合枚举。** `while mask: lowbit=mask&-mask; mask-=lowbit` 能逐个取出元素。
4. **GPU 搜索任务。** 小整数状态比棋盘数组更容易复制到线程局部状态或 shared memory 栈中。

## 常见误区

1. **忘记 `full &`。** 直接写 `~blocked` 会产生超出前 `N` 位的 1。
2. **列编号和位方向混淆。** 本系列约定第 0 列是最低位；画图时要保持一致。
3. **以为位运算只是小技巧。** 它实际上改变了状态表示，把集合判断变成机器整数操作。
4. **把 mask 当成无意义数字。** 每个 mask 都应能解释成一个集合，否则调试时很难定位错误。

## 检查点

给定 `N=4`，`cur=0101₂` 表示第 0 列和第 2 列已被占用。请计算 `full & ~cur`。答案是 `1010₂`，表示第 1 列和第 3 列仍未占用。

再试着枚举 `mask=1010₂` 的候选列：第一次 lowbit 是 `0010₂`，列号为 1；删除后剩 `1000₂`，第二次列号为 3。

## 参考资料

- Stanford Bit Twiddling Hacks：[Bit hacks](https://graphics.stanford.edu/~seander/bithacks.html)
- CP-Algorithms：[Submask enumeration](https://cp-algorithms.com/algebra/all-submasks.html)
- 参考项目：[ygch/n_queens](https://github.com/ygch/n_queens)

{% endraw %}
