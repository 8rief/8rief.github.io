---
layout: post
title: "Bellman-Ford：负边、松弛和负环检测"
date: 2026-06-25 14:05:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从 Dijkstra 的非负权边界出发，解释 Bellman-Ford 的重复松弛、负边处理、负环检测和随机 DAG 对照测试。"
tags: [algorithm, shortest-path, bellman-ford, negative-cycle, cplusplus]
---
{% raw %}
> 主题：Bellman-Ford / 负权边 / 负环检测 / C++ 可复现实验
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含固定最短路样例、可达负环样例和随机 DAG 对照。

Dijkstra 依赖一个强前提：边权非负。当前最小距离点被弹出后，后续路径不会再把它变小。引入负边后，这个前提失效，最短路需要另一种推进方式。

Bellman-Ford 的核心动作只有一个：松弛边。如果 `dist[u] + w < dist[v]`，就更新 `dist[v]`。一条不含重复点的最短路最多有 `n - 1` 条边，因此重复扫描所有边 `n - 1` 轮后，所有有限最短路都应稳定。第 `n` 轮仍然可以松弛，说明源点可达区域里存在负环。

## 学习目标

1. 明确 Dijkstra 和 Bellman-Ford 的适用边界。
2. 写出基于边表的松弛循环。
3. 用第 `n` 轮松弛检测可达负环。
4. 区分“不可达点”和“距离可以无限降低”。
5. 用 DAG 动态规划作为随机对照。

## 核心模型

![Bellman-Ford 重复松弛与负环检测](/assets/diagrams/algorithm-bellman-ford-negative-cycle.svg)

第 `k` 轮松弛结束后，所有最多使用 `k` 条边的最短路径信息都已经传播出来。这个按边数推进的视角，是 Bellman-Ford 正确性的主要来源。

## C++ 实现片段

```cpp
const long long INF = 4e18;

Result bellman_ford(int n, int source, const vector<Edge>& edges) {
    vector<long long> dist(n, INF);
    dist[source] = 0;

    for (int round = 0; round < n - 1; ++round) {
        bool changed = false;
        for (auto [u, v, w] : edges) {
            if (dist[u] == INF) continue;
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                changed = true;
            }
        }
        if (!changed) break;
    }

    bool negative_cycle = false;
    for (auto [u, v, w] : edges) {
        if (dist[u] != INF && dist[u] + w < dist[v]) {
            negative_cycle = true;
        }
    }
    return {dist, negative_cycle};
}
```

代码使用边表，原因是每一轮都要扫描所有边。`dist[u] == INF` 的检查很重要，它避免从不可达点传播无意义距离。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
distances from 0: 0 2 7 4 -2
negative_cycle=false
```

固定样例验证负边但无负环时的距离。另一个样例包含 `1 -> 2 -> 1` 的可达负环，测试要求 `negative_cycle=true`。随机 DAG 测试把边方向限制为从小编号指向大编号，再用拓扑顺序 DP 作为独立 oracle。

## 正确性思路

对轮数做归纳：第 0 轮只知道源点距离；第 1 轮后知道最多 1 条边的最短路径；第 `k` 轮后知道最多 `k` 条边的最短路径。没有负环时，一条最短简单路径最多经过 `n - 1` 条边，所以 `n - 1` 轮足够。

如果第 `n` 轮仍可松弛，就存在一条使用至少 `n` 条边还能变短的可达路径。根据抽屉原理，路径中有重复顶点；这段环的总权重必须为负，否则移除它不会让路径更短。

## 复杂度

- 时间：`O(nm)`。
- 空间：`O(n)`，如果只保存距离；保存前驱用于还原路径时仍为 `O(n)`。

## 常见错误

**把所有负环都当成结果失效。** 只有源点可达并能影响待求区域的负环才会让对应最短路无下界。本文检测的是源点可达负环。

**使用过小的 INF。** 多轮加法可能溢出。实际工程里要根据权重范围选择安全上界或做溢出检查。

**忘记提前退出。** 提前退出不影响正确性，可以明显减少普通图上的运行时间。

## 练习

1. 记录前驱数组，还原一条最短路。
2. 在检测到负环时输出环上的顶点。
3. 把算法改成 SPFA，并构造会退化的输入。
4. 解释 Johnson 全源最短路为什么需要 Bellman-Ford 计算势能。

## 参考资料

- [cp-algorithms: Bellman-Ford Algorithm](https://cp-algorithms.com/graph/bellman_ford.html)
- [Princeton Algorithms: Shortest Paths](https://algs4.cs.princeton.edu/44sp/)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
{% endraw %}
