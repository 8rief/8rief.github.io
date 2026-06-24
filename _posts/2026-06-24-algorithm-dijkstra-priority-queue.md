---
layout: post
title: "Dijkstra 最短路：用优先队列维护当前最可信的距离"
date: 2026-06-24 18:20:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用优先队列实现 Dijkstra 最短路，讲清非负边权前提、旧堆记录跳过、路径恢复和随机对照测试。"
tags: [algorithm, graph, dijkstra, priority-queue, cpp]
---
{% raw %}

> 主题：算法与数据结构 / Dijkstra / 图最短路 / priority_queue / C++ 实现  
> 本文命令已在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下本地执行验证。实验覆盖 Debug 构建、CTest、固定图最短路、不可达点、负边拒绝，以及随机非负图与 Bellman-Ford 参考实现对照。

最短路问题问的是：从一个源点出发，到图中每个点的最小路径代价是多少。Dijkstra 算法适合所有边权非负的场景。它的核心直觉是：如果当前所有候选路径中最短的是到 `u` 的距离，那么在边权非负的前提下，后续绕路不会把 `u` 的距离变得更小，所以可以把 `u` 的距离最终确定下来。

很多实现错误来自两个地方：第一，没有明确“边权非负”这个前提；第二，用 C++ `std::priority_queue` 时不会原地 decrease-key，于是堆里可能留下旧距离。本文把这两个点放进实现和测试里：发现负边直接拒绝；从堆里弹出旧记录时跳过。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 说明 Dijkstra 适用的图模型和非负边权前提。
2. 解释“弹出当前最小候选距离即可确定”的正确性直觉。
3. 用 `std::priority_queue` 写不需要 decrease-key 的 C++ 实现。
4. 处理不可达点、负边输入和路径恢复。
5. 用 Bellman-Ford 参考实现对随机非负图做对照测试。

## 问题模型

输入：一个有向加权图 `G = (V, E)`、源点 `source`。每条边 `u -> v` 有非负权重 `w`。

输出：从 `source` 到每个点的最短距离；如果不可达，距离记为无穷大。为了恢复路径，还可以记录每个点在当前最短路上的父节点。

本文还假设路径权重和不会超过 `long long` 的安全范围；如果边权来自不可信输入，生产代码需要额外做上界校验或溢出保护。本文使用邻接表：

```cpp
struct Edge {
    std::size_t to;
    long long weight;
};

using Graph = std::vector<std::vector<Edge>>;
```

`Graph[u]` 存储所有从 `u` 出发的边。边权用 `long long`，并用一个足够大的 `kInfinity` 表示不可达。

## 核心不变量

Dijkstra 维护三类点：

![Dijkstra 优先队列边界](/assets/diagrams/algorithm-dijkstra-frontier.svg)

1. 已确定点：它们的最短距离已经最终确定。
2. 候选点：已经找到一条从源点到它的路径，但还可能被更短路径更新。
3. 未发现点：当前还没有从源点到它的已知路径。

优先队列按候选距离从小到大弹出。每次弹出 `(dist, u)` 时，如果 `dist` 仍然等于当前记录的 `distance[u]`，就说明它是当前最小候选。由于所有边权非负，任何以后再经过其他候选点绕到 `u` 的路径都不会更短，所以 `u` 可以被确定。之后用 `u` 的出边尝试松弛邻居。

如果堆里弹出的 `dist` 不等于当前 `distance[u]`，说明这是旧记录。原因是某个点可能先以较长距离入堆，后来被更短路径更新并再次入堆。C++ 标准 `priority_queue` 没有直接 decrease-key 操作，常见做法就是允许重复入堆，并在弹出时跳过旧记录。

## C++ 实现

接口：

```cpp
#pragma once
#include <cstddef>
#include <limits>
#include <vector>

namespace graph {

struct Edge {
    std::size_t to;
    long long weight;
};

using Graph = std::vector<std::vector<Edge>>;

struct DijkstraResult {
    std::vector<long long> distance;
    std::vector<std::size_t> parent;
    std::size_t stale_pops = 0;
    std::size_t relaxations = 0;
};

constexpr long long kInfinity = std::numeric_limits<long long>::max() / 4;

DijkstraResult shortest_paths(const Graph& graph, std::size_t source);
std::vector<std::size_t> restore_path(const DijkstraResult& result, std::size_t target);

}  // namespace graph
```

实现主体：

```cpp
DijkstraResult shortest_paths(const Graph& graph, std::size_t source) {
    if (source >= graph.size()) {
        throw std::out_of_range("source vertex out of range");
    }
    for (std::size_t from = 0; from < graph.size(); ++from) {
        for (const auto& edge : graph[from]) {
            if (edge.to >= graph.size()) {
                throw std::out_of_range("edge target out of range");
            }
            if (edge.weight < 0) {
                throw std::invalid_argument("Dijkstra requires nonnegative edge weights");
            }
        }
    }

    DijkstraResult result;
    result.distance.assign(graph.size(), kInfinity);
    result.parent.assign(graph.size(), graph.size());
    using Item = std::pair<long long, std::size_t>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> heap;

    result.distance[source] = 0;
    result.parent[source] = source;
    heap.push({0, source});

    while (!heap.empty()) {
        const auto [dist, from] = heap.top();
        heap.pop();
        if (dist != result.distance[from]) {
            ++result.stale_pops;
            continue;
        }
        for (const auto& edge : graph[from]) {
            const long long candidate = dist + edge.weight;
            if (candidate < result.distance[edge.to]) {
                result.distance[edge.to] = candidate;
                result.parent[edge.to] = from;
                ++result.relaxations;
                heap.push({candidate, edge.to});
            }
        }
    }
    return result;
}
```

这里有三个工程细节：

- `std::priority_queue` 默认是大根堆，所以用 `std::greater<Item>` 变成小根堆。
- 每次更短距离出现时直接 `push` 新记录，不尝试在堆中删除旧记录。
- 弹出时用 `dist != result.distance[from]` 检查旧记录，旧记录不会参与松弛。

路径恢复沿着 `parent` 从目标点往源点走，再反转：

```cpp
std::vector<std::size_t> restore_path(const DijkstraResult& result, std::size_t target) {
    if (target >= result.distance.size()) {
        throw std::out_of_range("target vertex out of range");
    }
    if (result.distance[target] == kInfinity) {
        return {};
    }
    std::vector<std::size_t> path;
    std::size_t current = target;
    while (true) {
        path.push_back(current);
        if (result.parent[current] == current) {
            break;
        }
        current = result.parent[current];
    }
    std::reverse(path.begin(), path.end());
    return path;
}
```

不可达点返回空路径。源点的父节点设为自己，让恢复路径有明确终止条件。

## 验证策略

固定图测试先检查已知结果：

```cpp
void test_textbook_shape_graph() {
    graph::Graph g(6);
    g[0] = {{1, 7}, {2, 9}, {5, 14}};
    g[1] = {{2, 10}, {3, 15}};
    g[2] = {{3, 11}, {5, 2}};
    g[3] = {{4, 6}};
    g[5] = {{4, 9}};
    const auto result = graph::shortest_paths(g, 0);
    const std::vector<long long> expected{0, 7, 9, 20, 20, 11};
    require(result.distance == expected, "shortest distances");
    const auto path = graph::restore_path(result, 4);
    const std::vector<std::size_t> expected_path{0, 2, 5, 4};
    require(path == expected_path, "restore shortest path to 4");
}
```

边界测试检查不可达点和负边拒绝：

```cpp
void test_unreachable_and_invalid_inputs() {
    graph::Graph g(3);
    g[0] = {{1, 5}};
    const auto result = graph::shortest_paths(g, 0);
    require(result.distance[2] == graph::kInfinity, "unreachable distance is infinity");
    require(graph::restore_path(result, 2).empty(), "unreachable path is empty");

    bool negative_thrown = false;
    try {
        graph::Graph bad(2);
        bad[0] = {{1, -1}};
        (void)graph::shortest_paths(bad, 0);
    } catch (const std::invalid_argument&) {
        negative_thrown = true;
    }
    require(negative_thrown, "negative edge is rejected");
}
```

随机对照用 Bellman-Ford 作为参考实现。Bellman-Ford 更慢，但能处理非负图，也不依赖优先队列。小规模随机图上，把 Dijkstra 结果和 Bellman-Ford 结果逐源点比较，可以发现松弛条件、堆旧记录和不可达处理的很多错误。

```cpp
std::vector<long long> bellman_ford_reference(const graph::Graph& g, std::size_t source) {
    std::vector<long long> dist(g.size(), graph::kInfinity);
    dist[source] = 0;
    for (std::size_t iter = 1; iter < g.size(); ++iter) {
        bool changed = false;
        for (std::size_t from = 0; from < g.size(); ++from) {
            if (dist[from] == graph::kInfinity) {
                continue;
            }
            for (const auto& edge : g[from]) {
                const long long candidate = dist[from] + edge.weight;
                if (candidate < dist[edge.to]) {
                    dist[edge.to] = candidate;
                    changed = true;
                }
            }
        }
        if (!changed) {
            break;
        }
    }
    return dist;
}
```

## 执行实验

构建并测试：

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
```

本地输出：

```text
100% tests passed, 0 tests failed out of 1
```

运行示例程序：

```bash
./build/dijkstra_demo
```

输出：

```text
dist[0]=0 path=0
dist[1]=7 path=0->1
dist[2]=9 path=0->2
dist[3]=20 path=0->2->3
dist[4]=20 path=0->2->5->4
dist[5]=11 path=0->2->5
relaxations=7 stale_pops=2
```

`stale_pops=2` 说明堆里确实存在旧记录。它们不是错误；它们是“不做 decrease-key”的实现策略带来的正常现象。关键是弹出时要检查是否仍然等于当前最短距离。

## 正确性理由

Dijkstra 的关键断言是：在所有未确定点的候选距离中，最小的那个可以被最终确定。

设当前从堆里弹出点 `u`，候选距离为 `dist[u]`，并且它是所有候选中最小的。如果还存在一条更短路径到 `u`，这条路径必然从已确定区域出发，经过某个尚未确定的点 `x`，再走到 `u`。由于边权非负，从源点到 `x` 的距离不会大于整条路径到 `u` 的距离。这样 `x` 应该有一个比 `dist[u]` 更小的候选距离，和 `u` 是当前最小候选矛盾。因此 `u` 的距离可以确定。

每次确定一个点后，用它的出边更新邻居候选距离。循环结束时，所有可达点都被确定；没有被发现的点保持无穷大，表示不可达。

这个理由依赖非负边权。只要存在负边，后续绕路可能把已经弹出的点变得更短，算法不再可靠。因此本文实现直接拒绝负边输入。

## 复杂度

使用邻接表和二叉堆时：

- 每次松弛成功会向堆里插入一条记录，最多 `O(E)` 次；
- 每次堆操作成本 `O(log E)`；
- 扫描边的总成本是 `O(E)`。

因此总时间复杂度可写为 `O((V + E) log E)`，常见也写成 `O((V + E) log V)`，二者在简单图规模关系下可以互相转换。空间复杂度是 `O(V + E)`，包括图、距离、父节点和堆记录。

## 常见错误

**在有负边的图上使用 Dijkstra。** 负边会破坏“当前最小候选可以确定”的理由。需要处理负边时，应考虑 Bellman-Ford、SPFA 的适用边界，或 Johnson 算法等方案。

**忘记跳过旧堆记录。** 不做 decrease-key 时，同一个点可能多次入堆。弹出旧距离继续松弛，会浪费时间，某些写法还会覆盖父节点。

**把不可达点当成很大的真实距离。** `kInfinity` 只是哨兵。输出、路径恢复和加法前都要小心处理，避免把不可达路径当成有效结果。本文示例权重很小；如果真实输入可能接近整数上界，需要在松弛前检查 `dist + weight` 是否溢出。

**路径恢复没有源点终止条件。** `parent[source] = source` 是一个明确约定。没有这个约定，恢复路径时容易越界或死循环。

## 练习

1. 把图改成无向图：每条输入边同时加入 `u -> v` 和 `v -> u`，重新运行示例。
2. 输出每次弹堆和松弛的 trace，观察旧记录何时出现。
3. 把 `priority_queue` 实现换成 `std::set` 版本，显式删除旧候选距离，对比代码复杂度。
4. 在随机测试中加入负边，观察实现如何拒绝输入，再用 Bellman-Ford 单独处理这些图。

## 参考资料

- Edsger W. Dijkstra, “A note on two problems in connexion with graphs”, *Numerische Mathematik*, 1959. DOI: [10.1007/BF01386390](https://doi.org/10.1007/BF01386390)
- [cppreference: `std::priority_queue`](https://en.cppreference.com/w/cpp/container/priority_queue)
- [cp-algorithms: Dijkstra Algorithm](https://cp-algorithms.com/graph/dijkstra.html)
- Thomas H. Cormen et al., *Introduction to Algorithms*, 4th edition, chapter on single-source shortest paths.
{% endraw %}
