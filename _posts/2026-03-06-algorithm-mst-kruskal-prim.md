---
layout: post
title: "最小生成树：Kruskal、Prim 和安全边"
date: 2026-03-06 18:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从连通带权图的最低连接成本出发，解释安全边、Kruskal、Prim、DSU 校验和最小生成树的实验验证。"
tags: [algorithm, minimum-spanning-tree, kruskal, prim, cplusplus]
---
{% raw %}
> 主题：Minimum Spanning Tree / Kruskal / Prim / 安全边 / C++ 可复现实验
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含固定图和随机连通图，Kruskal 与 Prim 的结果相互校验。

很多图问题都可以理解成“选择一些边，同时保持某种结构”。最小生成树的结构要求很清楚：在一个无向连通带权图里，选择 `n - 1` 条边，把所有顶点连起来，并让总权重最小。

这个问题适合用来训练贪心证明。代码本身很短，真正关键的是安全边：当一个割把顶点分成两侧时，跨过这个割的最轻边可以被某棵最小生成树包含。Kruskal 从全局最轻边开始防止成环，Prim 从一个已选集合向外扩展，它们使用的是同一类安全选择。

## 为什么需要安全边证明

“每次选最便宜的边”本身并不总是正确；如果不检查结构，便宜边可能形成环，浪费一个名额。MST 的贪心能成立，是因为每一步都能解释为某个割上的最轻跨边：把当前已经确认的一侧和另一侧分开，跨过这个割的最轻边可以安全加入。

这个交换论证消除了局部选择的风险。若一棵最优树没有选这条最轻跨边，把它加入会形成一个环；环上必有另一条跨过同一割的边，删掉那条不更轻的边，仍是一棵生成树且总权重不增。

## 学习目标

1. 说清楚生成树、割、环和安全边的关系。
2. 用 DSU 实现 Kruskal，避免选择形成环的边。
3. 用优先队列实现 Prim，每次扩展当前集合的最轻出边。
4. 用随机图比较两种算法输出，发现实现错误。
5. 解释复杂度和适用场景。

## 核心模型

![最小生成树的两种贪心视角](/assets/diagrams/algorithm-mst-kruskal-prim.svg)

Kruskal 的视角是“边从小到大进入候选池”；Prim 的视角是“当前连通块向外扩张”。前者天然需要 DSU 判断两个端点是否已经连通，后者天然需要优先队列维护跨出当前集合的最小边。

固定图边集为：

```text
0-1(4), 0-2(3), 1-2(1), 1-3(2), 2-3(4), 3-4(2), 2-4(5)
```

Kruskal 按权重排序后依次选择：

```text
1-2(1)  -> 连接 {1},{2}
1-3(2)  -> 把 3 接入
3-4(2)  -> 把 4 接入
0-2(3)  -> 把 0 接入，总权重 8
```

后面的 `0-1(4)`、`2-3(4)` 和 `2-4(5)` 都会连接已经同属一个连通分量的点，因此被 DSU 拒绝。

## C++ 实现片段

```cpp
struct DSU {
    vector<int> parent, size;
    explicit DSU(int n) : parent(n), size(n, 1) {
        iota(parent.begin(), parent.end(), 0);
    }
    int find(int x) {
        return parent[x] == x ? x : parent[x] = find(parent[x]);
    }
    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (size[a] < size[b]) swap(a, b);
        parent[b] = a;
        size[a] += size[b];
        return true;
    }
};

long long kruskal(int n, vector<Edge> edges) {
    sort(edges.begin(), edges.end(), [](auto& a, auto& b) {
        return a.w < b.w;
    });
    DSU dsu(n);
    long long total = 0;
    int used = 0;
    for (auto e : edges) {
        if (dsu.unite(e.u, e.v)) {
            total += e.w;
            ++used;
        }
    }
    assert(used == n - 1);
    return total;
}
```

Prim 的实现可以把所有从已选集合出发的边放入小根堆。堆里会残留一些已经指向已选点的旧边，弹出时跳过即可。

同一张图上，Prim 从 0 出发时先选 `0-2(3)`，随后堆中出现 `2-1(1)`，再选 `1-3(2)` 和 `3-4(2)`，总权重同样是 8。边集顺序与 Kruskal 不同，但都满足每一步取当前割的最轻跨边。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
Kruskal MST weight=8
Prim MST weight=8
MST keeps the cheapest safe edge across a cut without forming a cycle
```

固定图检查结果权重为 8，并额外检查不连通图返回空结果。随机测试使用 seed `20260625` 生成 300 个连通图：先用链 `0-1-...-n-1` 保证连通，再补充随机边，随后比较 Kruskal 和 Prim 的总权重。两种独立实现得到同一结果，比只跑一个样例更能暴露排序、DSU 合并、堆弹出和连通性处理错误。

## 正确性思路

Kruskal 每次选择连接两个不同连通分量的最轻可用边。把当前分量看成割的一侧时，这条边是某个割上的最轻跨边，因此是安全边。加入它不会破坏存在某棵最小生成树包含已选边的归纳假设。

Prim 每次从已选集合跨向未选集合选择最轻边。这个边同样是当前割的最轻跨边。加入新点后，已选集合扩大，继续维护同一安全选择逻辑。

## 复杂度

- Kruskal：排序 `O(m log m)`，DSU 近似 `O(m α(n))`。
- Prim：邻接表加优先队列通常为 `O(m log m)`，也常写作 `O(m log n)`。
- 空间：图和辅助结构为 `O(n + m)`。

稠密图上，邻接矩阵版本 Prim 可以做到 `O(n²)`，不一定比堆版本差。边数远小于 `n²` 时，Kruskal 或堆优化 Prim 更自然。

## 输入和结果边界

- MST 定义在无向图上；有向图对应的是最小树形图，不能直接套 Kruskal/Prim。
- 图不连通时不存在生成树，实验函数返回 `nullopt`，而不是返回部分森林权重。
- 边权可以相等，因此 MST 的边集可能不唯一；通常只要求总权重最小。
- 示例代码用 `int` 保存总权重，边权和规模大时应改成 `long long`。

## 常见错误

**只检查边数，不检查连通性。** 输入如果不连通，无法形成生成树。实验代码在 `used == n - 1` 时才接受结果。

**Prim 把无向边只加入一侧。** 无向图邻接表需要双向加入；否则从某些起点无法看到完整边界。

**Kruskal 忘记跳过同一连通分量。** 这会形成环，结果边数可能超过 `n - 1`。

**把 Prim 堆顶边直接加入答案。** 堆中可能有旧边指向已选点，必须弹出后检查 `seen[u]`。

## 练习

1. 输出最小生成树的边集，而不只输出总权重。
2. 支持图不连通时返回最小生成森林。
3. 构造边权相同的图，观察不同合法 MST 的边集差异。
4. 比较稠密图上 Prim 邻接矩阵版本和堆版本的表现。

## 参考资料

- [cp-algorithms: Minimum Spanning Tree - Kruskal](https://cp-algorithms.com/graph/mst_kruskal.html)
- [cp-algorithms: Minimum Spanning Tree - Prim](https://cp-algorithms.com/graph/mst_prim.html)
- [Princeton Algorithms: Minimum Spanning Trees](https://algs4.cs.princeton.edu/43mst/)
- [cppreference: std::priority_queue](https://en.cppreference.com/w/cpp/container/priority_queue)
{% endraw %}
