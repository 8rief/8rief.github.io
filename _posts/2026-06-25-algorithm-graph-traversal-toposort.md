---
layout: post
title: "图遍历和拓扑排序：先学会系统地走完整张图"
date: 2026-06-25 05:25:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用 BFS、DFS 和 Kahn 拓扑排序建立图算法基础，解释访问状态、层次距离、依赖顺序和有向环检测。"
tags: [algorithm, graph, bfs, dfs, topological-sort, cplusplus]
---
{% raw %}

> 主题：图遍历 / BFS / DFS / 拓扑排序 / C++ 可复现实验  
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含固定图、环检测和随机 DAG 拓扑序验证。

前面已经写过 Dijkstra，但图算法不能从最短路直接开始。最短路、连通性、强连通分量、最小生成树、网络流，本质上都离不开“如何系统地访问图”。BFS、DFS 和拓扑排序是图算法的底层动作。

BFS 按层推进，适合无权最短路和层次扩展；DFS 沿路径深入，适合连通分量、回溯、时间戳和结构分析；拓扑排序处理有向无环图中的依赖顺序，同时可以检测环。

## 学习目标

1. 用邻接表表示图。
2. 写出 BFS 的距离数组和队列不变量。
3. 写出 DFS 的访问状态与先序遍历。
4. 用入度和队列实现 Kahn 拓扑排序。
5. 判断一个拓扑序是否满足所有边的依赖方向。

## 核心模型

![图遍历和拓扑排序](/assets/diagrams/algorithm-graph-traversal-toposort.svg)

BFS 的队列里保存已经发现但尚未扩展的点。DFS 的递归栈保存当前路径。拓扑排序的队列保存当前入度为 0、已经没有前置依赖的点。

## BFS：无权图层次距离

```cpp
std::vector<int> bfs_distances(const std::vector<std::vector<int>>& g,
                               int source) {
    std::vector<int> dist(g.size(), -1);
    std::queue<int> q;
    dist[source] = 0;
    q.push(source);
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int v : g[u]) if (dist[v] == -1) {
            dist[v] = dist[u] + 1;
            q.push(v);
        }
    }
    return dist;
}
```

`dist[v] == -1` 同时表示未访问。第一次访问到 `v` 时，它一定来自最少边数路径，因为 BFS 按距离层逐层推进。

## DFS：沿路径深入

```cpp
void dfs_visit(const std::vector<std::vector<int>>& g,
               int u,
               std::vector<int>& seen,
               std::vector<int>& order) {
    seen[u] = 1;
    order.push_back(u);
    for (int v : g[u]) {
        if (!seen[v]) dfs_visit(g, v, seen, order);
    }
}
```

DFS 的输出顺序受邻接表顺序影响。很多图算法真正使用的是访问状态、递归树、进入/退出时间和边类型。

## Kahn 拓扑排序

```cpp
std::optional<std::vector<int>> topological_sort(
    const std::vector<std::vector<int>>& g) {
    int n = static_cast<int>(g.size());
    std::vector<int> indeg(n, 0);
    for (int u = 0; u < n; ++u) for (int v : g[u]) ++indeg[v];

    std::queue<int> q;
    for (int i = 0; i < n; ++i) if (indeg[i] == 0) q.push(i);

    std::vector<int> order;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        order.push_back(u);
        for (int v : g[u]) if (--indeg[v] == 0) q.push(v);
    }
    if (static_cast<int>(order.size()) != n) return std::nullopt;
    return order;
}
```

如果图里有环，环上的点不会全部降到入度 0，最终输出点数少于 `n`。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
BFS distances from 0: 0 1 1 2 3
topological order: 0 1 2 3 4
```

测试包含固定图的 BFS 距离、DFS 先序、拓扑排序合法性、有向环检测，以及 200 轮随机 DAG。随机 DAG 的拓扑序用位置数组验证：每条边 `u -> v` 都必须满足 `pos[u] < pos[v]`。

## 正确性思路

BFS 的正确性来自队列层次：距离为 `d` 的点扩展完之前，距离为 `d+1` 的点不会继续扩展到更深层，因此第一次发现就是最短边数。

拓扑排序的正确性来自入度含义：入度为 0 的点没有未处理前置依赖，可以安全输出。输出后删除它的出边，可能让后继变成新的可输出点。如果所有点都能输出，顺序满足所有依赖；如果不能，剩余边构成环或环相关结构。

## 复杂度

BFS、DFS 和 Kahn 拓扑排序都在邻接表上运行，时间复杂度 `O(V + E)`，空间复杂度 `O(V)` 加上图本身存储。

## 常见错误

**用 BFS 处理带权最短路。** BFS 只适用于无权图或所有边权相同的图。非负权最短路才使用 Dijkstra。

**递归 DFS 爆栈。** 深图上可以改成显式栈，或控制递归深度。

**拓扑排序结果不唯一。** 多个入度为 0 的点可以任意选择，合法拓扑序通常不唯一。

## 练习

1. 用 BFS 求无权图从 `s` 到 `t` 的具体路径。
2. 把 DFS 改成迭代版本。
3. 用 DFS 三色标记检测有向环。
4. 用拓扑序求 DAG 上的最长路径。

## 参考资料

- [MIT OpenCourseWare 6.006 Syllabus](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/pages/syllabus/)
- [Princeton Algorithms, Part II](https://algs4.cs.princeton.edu/home/i)
- [cp-algorithms: Breadth First Search](https://cp-algorithms.com/graph/breadth-first-search.html)
- [cp-algorithms: Topological Sorting](https://cp-algorithms.com/graph/topological-sort.html)
{% endraw %}
