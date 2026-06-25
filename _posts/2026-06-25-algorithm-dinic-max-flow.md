---
layout: post
title: "Dinic 最大流：层次图、阻塞流和最小割"
date: 2026-06-25 14:15:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从残量网络出发解释 Dinic 的 BFS 层次图、DFS 阻塞流、最大流终止条件和 Edmonds-Karp 随机对照。"
tags: [algorithm, max-flow, dinic, graph, cplusplus]
---
{% raw %}
> 主题：Dinic / 最大流 / 残量网络 / 层次图 / C++ 可复现实验
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含经典网络、随机小图和 Edmonds-Karp 对照。

最大流问题描述的是容量受限网络中，从源点 `s` 向汇点 `t` 最多能发送多少流量。它的关键抽象是残量网络：每次发送流量后，正向边容量减少，反向边容量增加，反向边表示将来可以撤销部分选择。

Dinic 在残量网络上分阶段推进。每一阶段先用 BFS 建立层次图，只保留从第 `k` 层指向第 `k+1` 层的边；再用 DFS 在层次图里寻找阻塞流。层次图中再也找不到增广路时，重新 BFS。

## 学习目标

1. 理解流量守恒、容量限制和残量边。
2. 写出 Dinic 的 BFS 层次图和 DFS 增广。
3. 说明阻塞流为什么能批量推进多个增广路径。
4. 用 Edmonds-Karp 作为随机小图 oracle。
5. 通过残量可达集合理解最小割。

## 核心模型

![Dinic 最大流阶段](/assets/diagrams/algorithm-dinic-max-flow.svg)

残量网络保留所有“还能调整”的选择。BFS 层次图防止 DFS 在同一阶段走回头路，`ptr` 当前弧优化则避免反复扫描已经耗尽的边。

## C++ 实现片段

```cpp
struct Edge { int to, rev; long long cap; };

class Dinic {
    vector<vector<Edge>> g;
    vector<int> level, ptr;

    bool bfs(int s, int t) {
        fill(level.begin(), level.end(), -1);
        queue<int> q;
        level[s] = 0;
        q.push(s);
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (auto& e : g[u]) {
                if (e.cap > 0 && level[e.to] == -1) {
                    level[e.to] = level[u] + 1;
                    q.push(e.to);
                }
            }
        }
        return level[t] != -1;
    }

    long long dfs(int u, int t, long long pushed) {
        if (u == t || pushed == 0) return pushed;
        for (int& cid = ptr[u]; cid < (int)g[u].size(); ++cid) {
            Edge& e = g[u][cid];
            if (e.cap <= 0 || level[e.to] != level[u] + 1) continue;
            long long f = dfs(e.to, t, min(pushed, e.cap));
            if (!f) continue;
            e.cap -= f;
            g[e.to][e.rev].cap += f;
            return f;
        }
        return 0;
    }
};
```

边结构里的 `rev` 指向反向边下标。每次增广都同时修改正向残量和反向残量，这是流算法实现里最容易漏掉的状态变化。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
max flow=23
reachable after maxflow: 0 1 2 4
```

固定网络的最大流为 23。随机测试在小规模有向图上比较 Dinic 与 Edmonds-Karp。最大流结束后，从源点沿正残量边可达的点集给出一个最小割的源侧集合，实验输出中的 `0 1 2 4` 就是该样例的可达侧。

## 正确性思路

每次 DFS 增广都沿残量网络中的合法路径发送流，容量限制和流量守恒由正反边更新维护。BFS 找不到从 `s` 到 `t` 的残量路径时，根据最大流最小割定理，当前流已经达到某个割的容量，因此是最大流。

Dinic 的层次图保证一个阶段内只沿最短层次增广。阻塞流完成后，这个层次图上的所有 `s-t` 路径都被堵住；下一次 BFS 若仍可达，汇点层数会推进，算法最终终止。

## 复杂度

一般图上 Dinic 的常见上界是 `O(V^2 E)`。在二分图匹配等特殊网络上有更强界。实际使用时，它比逐条最短增广路的 Edmonds-Karp 通常快很多。

## 常见错误

**反向边没有同步更新。** 没有反向残量就无法撤销早期选择，结果可能小于最大流。

**DFS 不使用引用当前弧。** `ptr[u]` 应该记住已经扫描失败的边，避免同一阶段反复尝试。

**容量类型过小。** 多条边累加可能超过 `int`。本文用 `long long` 存容量和总流。

## 练习

1. 用 Dinic 求二分图最大匹配。
2. 输出一个最小割：列出从可达侧指向不可达侧的原图边。
3. 增加下界流量约束，了解可行流建模。
4. 用同一个接口实现 Edmonds-Karp，对比随机图耗时。

## 参考资料

- [cp-algorithms: Dinic's algorithm](https://cp-algorithms.com/graph/dinic.html)
- [Princeton Algorithms: Maxflow](https://algs4.cs.princeton.edu/64maxflow/)
- [cppreference: std::queue](https://en.cppreference.com/w/cpp/container/queue)
{% endraw %}
