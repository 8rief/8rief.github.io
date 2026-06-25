---
layout: post
title: "倍增 LCA：用二进制祖先回答树上最近公共祖先"
date: 2026-06-25 14:35:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "把树上父指针扩展成二进制祖先表，解释深度对齐、同步上跳、距离查询和随机树朴素对照。"
tags: [algorithm, lca, binary-lifting, tree, cplusplus]
---
{% raw %}
> 主题：LCA / binary lifting / tree query / C++ 可复现实验
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含固定树查询和随机树朴素对照。

树上两个点的最近公共祖先（Lowest Common Ancestor, LCA）是很多路径问题的基础。求出 LCA 后，路径长度、路径聚合、树上差分和虚树构造都会变得更直接。

倍增法的想法很朴素：既然每个点有父节点，就可以预处理它的 `2^0`、`2^1`、`2^2` 级祖先。查询时先把深度较大的点向上跳到同一深度，再从大到小尝试同步上跳，直到两个点的父节点相同。

## 学习目标

1. 建立根树、深度和父节点数组。
2. 预处理 `up[v][k]`，表示 `v` 的 `2^k` 级祖先。
3. 实现按二进制拆分的 `lift(v, d)`。
4. 实现 LCA 查询和树上距离查询。
5. 用随机树上的朴素祖先集方法验证结果。

## 核心模型

![倍增 LCA 查询流程](/assets/diagrams/algorithm-binary-lifting-lca.svg)

`up[v][k] = up[ up[v][k-1] ][k-1]`。这个转移把两段 `2^{k-1}` 祖先拼成一段 `2^k` 祖先。

## C++ 实现片段

```cpp
class LCA {
    int n, logn;
    vector<int> depth;
    vector<vector<int>> up;
    vector<vector<int>> g;

    void dfs(int u, int p) {
        up[u][0] = p;
        for (int k = 1; k < logn; ++k) {
            up[u][k] = up[up[u][k - 1]][k - 1];
        }
        for (int v : g[u]) {
            if (v == p) continue;
            depth[v] = depth[u] + 1;
            dfs(v, u);
        }
    }

    int lift(int v, int d) const {
        for (int k = 0; d; ++k, d >>= 1) {
            if (d & 1) v = up[v][k];
        }
        return v;
    }
};
```

根节点的父节点可以设成自己，这样向上跳时不会遇到 `-1`。如果使用 `-1`，所有转移都要额外判断，代码更容易分叉。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
lca(4,7)=1
lca(5,6)=2
dist(7,6)=5
```

固定树检查常见查询；随机测试生成父节点编号小于子节点编号的树，用朴素方法构造一个点到根的祖先集合，再向上走另一个点找到第一个公共祖先。倍增结果必须与朴素结果一致。

## 正确性思路

深度对齐后，两个点位于同一层。若它们相等，当前点就是 LCA。若不相等，从大到小枚举 `k`，当 `up[a][k] != up[b][k]` 时同时上跳，保证跳过的祖先仍在 LCA 下方。

循环结束后，`a` 和 `b` 已经是 LCA 的不同子树中的最高点，它们的父节点相同，这个父节点就是最近公共祖先。

距离公式来自树路径分解：`dist(a,b) = depth[a] + depth[b] - 2 * depth[lca(a,b)]`。

## 复杂度

- 预处理：`O(n log n)`。
- 单次 LCA 查询：`O(log n)`。
- 距离查询：一次 LCA 后 `O(1)` 组合。
- 空间：`O(n log n)`。

## 常见错误

**根节点父指针处理不一致。** 推荐令根的所有祖先都指向根，避免查询时越界。

**LOG 取值过小。** 需要满足 `2^LOG >= n`。常见写法是循环增加直到 `(1 << LOG) > n`。

**先同步上跳再判断相等。** 深度对齐后要先检查 `a == b`，否则祖先关系查询会返回父节点。

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
