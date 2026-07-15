---
layout: post
title: "倍增 LCA：用二进制祖先回答树上最近公共祖先"
date: 2026-03-10 18:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "把树上父指针扩展成二进制祖先表，解释深度对齐、同步上跳、距离查询和随机树朴素对照。"
tags: [algorithm, lca, binary-lifting, tree, cplusplus]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithms-binary-lifting-lca/README.md`](/assets/labs/algorithms-binary-lifting-lca/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：LCA / binary lifting / tree query / C++ 可复现实验
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含固定树查询和随机树朴素对照。

树上两个点的最近公共祖先（Lowest Common Ancestor, LCA）是很多路径问题的基础。求出 LCA 后，路径长度、路径聚合、树上差分和虚树构造都会变得更直接。

倍增法的想法很朴素：既然每个点有父节点，就可以预处理它的 `2^0`、`2^1`、`2^2` 级祖先。查询时先把深度较大的点向上跳到同一深度，再从大到小尝试同步上跳，直到两个点的父节点相同。

逐级沿父指针查询在链状树上需要 `O(n)` 时间。倍增法先付出 `O(n log n)` 预处理成本，把每次查询压到 `O(log n)`，适合静态树上有大量 LCA 或距离查询的场景。

## 学习目标

1. 建立根树、深度和父节点数组。
2. 预处理 `up[v][k]`，表示 `v` 的 `2^k` 级祖先。
3. 实现按二进制拆分的 `lift(v, d)`。
4. 实现 LCA 查询和树上距离查询。
5. 用随机树上的朴素祖先集方法验证结果。

## 核心模型

![倍增 LCA 查询流程](/assets/diagrams/algorithm-binary-lifting-lca.svg)

当前源码按 `up[k][v]` 存储，其中 `up[k][v]` 是节点 `v` 的 `2^k` 级祖先：

```text
up[k][v] = up[k-1][ up[k-1][v] ]
```

这个转移把两段 `2^{k-1}` 祖先拼成一段 `2^k` 祖先。本文所有预处理、上跳和查询代码统一使用 `up[k][v]`，避免两个维度在不同函数中交换。

## 为什么要引入二进制祖先表

任意非负上跳距离 `d` 都能拆成不同二次幂之和。例如 `13=8+4+1`，只需依次使用 `up[3]`、`up[2]`、`up[0]`，不必走 13 次父指针。

若树有 `n` 个节点，只需保存到 `2^k>n`。固定样例 `n=8` 时，源码得到 `LOG=4`，可表示 1、2、4、8 级跳跃。

## 预处理状态怎样建立

源码先从 parent 数组构造子节点邻接表，再从唯一根开始 DFS：

## C++ 实现片段

```cpp
class LCA {
    int n, LOG;
    vector<int> depth;
    vector<vector<int>> up;
    vector<vector<int>> g;

    void dfs(int u, int p) {
        up[0][u] = p;
        for (int k = 1; k < LOG; ++k) {
            up[k][u] = up[k - 1][up[k - 1][u]];
        }
        for (int v : g[u]) {
            depth[v] = depth[u] + 1;
            dfs(v, u);
        }
    }

    int lift(int v, int d) const {
        for (int k = 0; d; ++k, d >>= 1) {
            if (d & 1) v = up[k][v];
        }
        return v;
    }
};
```

根节点的父节点设成自己，这样任意过量上跳都会停在根，不会索引 `-1`。输入 parent 数组中的根仍用 `-1` 标识；构造 `up` 表时才改为自环。

固定 parent 数组是：

```text
node:    0  1 2 3 4 5 6 7
parent: -1  0 0 1 1 2 2 3
depth:   0  1 1 2 2 2 2 3
```

节点 7 的祖先表为 `up[0][7]=3`、`up[1][7]=1`、`up[2][7]=0`、`up[3][7]=0`。

## 查询状态怎样变化

LCA 查询分两阶段：

```cpp
if (depth[a] < depth[b]) std::swap(a, b);
a = lift(a, depth[a] - depth[b]);
if (a == b) return a;
for (int k = LOG - 1; k >= 0; --k) {
    if (up[k][a] != up[k][b]) {
        a = up[k][a];
        b = up[k][b];
    }
}
return up[0][a];
```

第一阶段只移动较深节点，保持“LCA 不变”；第二阶段从最大跳幅向下尝试，只在两点跳后仍不相等时接受跳跃，因此两点始终留在真实 LCA 下方。

## 实验输出怎样解释

```text
100% tests passed, 0 tests failed out of 1
lca(4,7)=1
lca(5,6)=2
dist(7,6)=5
```

固定树检查常见查询；随机测试生成父节点编号小于子节点编号的树，用朴素方法构造一个点到根的祖先集合，再向上走另一个点找到第一个公共祖先。倍增结果必须与朴素结果一致。

`lca(4,7)` 的状态为：

```text
depth[4]=2, depth[7]=3
先把 7 上跳 1 层到 3
3 与 4 不同，但它们的 1 级祖先都是 1
因此 LCA=1
```

`lca(5,6)=2`，因为二者父节点相同。`7` 到 `6` 的 LCA 是根 0，所以距离为 `3+2-2×0=5`。

复跑入口：

```bash
./run_lab.sh
```

CTest 固定检查三条查询，并以 seed 20260625 生成 200 棵、规模 1 到 200 的随机树；每棵执行 300 次倍增与朴素 LCA 对照，共 60000 次随机查询。

## 正确性思路

深度对齐后，两个点位于同一层。若它们相等，当前点就是 LCA。若不相等，从大到小枚举 `k`，当 `up[a][k] != up[b][k]` 时同时上跳，保证跳过的祖先仍在 LCA 下方。

循环结束后，`a` 和 `b` 已经是 LCA 的不同子树中的最高点，它们的父节点相同，这个父节点就是最近公共祖先。

距离公式来自树路径分解：`dist(a,b) = depth[a] + depth[b] - 2 * depth[lca(a,b)]`。

这里的“不接受跳到相同祖先”是正确性的关键：若 `up[k][a]==up[k][b]`，这个共同祖先可能已经等于或高于 LCA，继续跳会越过答案。

## 复杂度

- 预处理：`O(n log n)`。
- 单次 LCA 查询：`O(log n)`。
- 距离查询：一次 LCA 后 `O(1)` 组合。
- 空间：`O(n log n)`。

## 常见错误

**根节点父指针处理不一致。** 推荐令根的所有祖先都指向根，避免查询时越界。

**LOG 取值过小。** 需要满足 `2^LOG >= n`。常见写法是循环增加直到 `(1 << LOG) > n`。

**先同步上跳再判断相等。** 深度对齐后要先检查 `a == b`，否则祖先关系查询会返回父节点。

**把表的两个维度混写。** 当前实现固定使用 `up[k][v]`；若改成 `up[v][k]`，预处理、lift 和 LCA 三处必须一起调整。

**输入不是合法根树。** 当前教学实现假设恰有一个 `-1` 根、每个其他节点有合法父节点且无环；构造器没有做完整输入验证。

**递归 DFS 栈过深。** 极长链可能耗尽调用栈；大规模工程输入应改成显式栈或迭代遍历。

## 练习

1. 给每条边加权，维护根到点距离，回答路径权重和。
2. 在 `up` 表旁边维护路径最大边权，回答树上最大边查询。
3. 实现 Euler Tour + RMQ 版本 LCA，并和倍增法比较。
4. 在动态加叶子的场景下维护倍增表。

## 参考资料

- [cp-algorithms: Lowest Common Ancestor - Binary Lifting](https://cp-algorithms.com/graph/lca_binary_lifting.html)
- [Princeton Algorithms: Graphs](https://algs4.cs.princeton.edu/40graphs/)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
{% endraw %}
