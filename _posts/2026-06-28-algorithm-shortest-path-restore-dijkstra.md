---
layout: post
title: "最短路路径恢复：让距离数组变成可解释路线"
date: 2026-06-28 21:46:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "在 Dijkstra 距离数组之外记录 predecessor，恢复从源点到目标点的一条最短路径。"
tags: [algorithm, dijkstra, shortest-path, predecessor, cpp]
---
{% raw %}

> 主题：算法实用基础 / shortest path / path restoration  
> 本文 lab 已验证：源点 0 到目标 4 的距离为 6，恢复路径为 `0->1->3->4`。

很多最短路文章只输出距离，但实际问题经常需要路径：导航要给出路线，依赖分析要给出链路，调试图模型时要解释答案怎么来的。路径恢复的关键是在松弛成功时记录 predecessor，也就是当前最短路径中到达该点的前一个点。

## 问题模型

输入是非负边权图、源点和目标点。输出包括源点到每个点的最短距离，以及源点到目标点的一条最短路径。如果目标不可达，路径为空，距离保持无穷大标记。

## 核心不变量

![Dijkstra predecessor 路径恢复模型](/assets/diagrams/algorithm-shortest-path-restore-dijkstra.svg)

Dijkstra 的距离不变量是：优先队列弹出的当前最小距离点已经确定最短距离。路径恢复增加一个不变量：每次 `dist[v]` 被更短路径更新时，`parent[v]` 记录让这次更新成立的前驱点 u。最终沿 parent 从目标反向走，就得到一条最短路。

## 正确性理由

松弛边 `u -> v` 时，如果 `dist[u] + w < dist[v]`，说明经过 u 能得到更短的 v 路径。此时把 `parent[v]` 设为 u，记录的是当前最优路径的最后一条边。Dijkstra 结束后，目标点距离不再变化，沿 parent 反向经过的每条边都来自某次最短距离更新，因此反转后就是一条从源点到目标点的最短路径。

## 复杂度分析

使用邻接表和优先队列时，Dijkstra 的时间复杂度是 `O((V + E) log V)`，空间复杂度是 `O(V + E)`。`parent` 数组只增加 `O(V)` 空间。路径恢复本身沿目标路径走一遍，时间是路径长度 `O(L)`。

## C++ 实现

```cpp
vector<int> dist(n, inf), parent(n, -1);
priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;
dist[source] = 0;
pq.push({0, source});

while (!pq.empty()) {
    auto [d, node] = pq.top();
    pq.pop();
    if (d != dist[node]) continue;
    for (auto [next, weight] : graph[node]) {
        if (dist[next] > d + weight) {
            dist[next] = d + weight;
            parent[next] = node;
            pq.push({dist[next], next});
        }
    }
}
```

恢复路径：

```cpp
vector<int> path;
if (dist[target] < inf) {
    for (int cur = target; cur != -1; cur = parent[cur]) path.push_back(cur);
    reverse(path.begin(), path.end());
}
```

## 测试与边界

lab 输出：

```text
dijkstra_distance_0_4=6 path=0->1->3->4
```

边界包括源点等于目标、目标不可达、多条等长最短路、零权边、负权边。Dijkstra 要求边权非负；如果存在负权边，应使用 Bellman-Ford 或其他适合的算法。

## 练习

1. 让图中出现两条等长最短路，观察 parent 如何受邻接表顺序影响。
2. 增加不可达目标，要求输出空路径。
3. 把路径恢复封装成函数，并检查恢复路径的边权和是否等于 `dist[target]`。

## 参考资料

- CP-Algorithms：[Dijkstra Algorithm](https://cp-algorithms.com/graph/dijkstra.html)
- CP-Algorithms：[Dijkstra on sparse graphs](https://cp-algorithms.com/graph/dijkstra_sparse.html)
- cppreference：[std::priority_queue](https://en.cppreference.com/w/cpp/container/priority_queue)

{% endraw %}
