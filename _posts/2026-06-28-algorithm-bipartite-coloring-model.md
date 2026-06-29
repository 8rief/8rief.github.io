---
layout: post
title: "二分图染色：先判断冲突，再谈匹配"
date: 2026-06-28 21:45:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用 BFS/DFS 染色讲清二分图建模、奇环冲突和匹配算法之前必须固定的问题边界。"
tags: [algorithm, bipartite-graph, graph-coloring, cpp, bfs]
---
{% raw %}

> 主题：算法实用基础 / bipartite graph / coloring  
> 本文 lab 已验证：四点偶环可以二分染色，三角形会记录冲突边。

二分图常出现在“把对象分成两侧”的问题里：课程和学生、任务和机器、左括号和右括号。进入匹配算法之前，先要会判断一个图是否真的能分成两侧。染色法是最直接的基础模型：相邻点必须颜色不同。

## 问题模型

输入是一个无向图。输出是是否存在一种 0/1 染色，使得每条边的两个端点颜色不同。如果不存在，输出一条冲突边帮助定位问题。这个判断等价于图中没有奇数长度环。

## 核心不变量

![二分图染色不变量](/assets/diagrams/algorithm-bipartite-coloring-model.svg)

从任意未染色点开始，把它染成 0；访问一条边 `u-v` 时，如果 v 未染色，就染成 `color[u] ^ 1`；如果 v 已染色，它必须和 u 颜色相反。队列或递归栈中的每个点都已经有颜色。

## 正确性理由

沿路径传播颜色时，路径长度决定颜色奇偶。如果一条边连接了同色点，就表示存在两条奇偶性冲突的路径，合起来形成奇环，因此无法二分。反过来，如果所有边都连接异色点，颜色 0 的点和颜色 1 的点自然构成二分图的两侧。

## 复杂度分析

每个点最多染色一次，每条边最多检查两次。邻接表实现的时间复杂度是 `O(V + E)`，空间复杂度是 `O(V)`。图可能不连通，所以需要从每个未染色点启动一次 BFS 或 DFS。

## C++ 实现

```cpp
BipartiteResult color_bipartite(const vector<vector<int>>& graph) {
    BipartiteResult result;
    result.color.assign(graph.size(), -1);
    for (int start = 0; start < static_cast<int>(graph.size()); ++start) {
        if (result.color[start] != -1) continue;
        queue<int> q;
        result.color[start] = 0;
        q.push(start);
        while (!q.empty()) {
            int node = q.front();
            q.pop();
            for (int next : graph[node]) {
                if (result.color[next] == -1) {
                    result.color[next] = result.color[node] ^ 1;
                    q.push(next);
                } else if (result.color[next] == result.color[node]) {
                    result.ok = false;
                    result.conflict = {node, next};
                    return result;
                }
            }
        }
    }
    return result;
}
```

## 测试与边界

lab 验证了偶环和三角形：

```text
bipartite_square=true triangle=false
```

边界包括空图、孤立点、多个连通块、自环、重复边。自环会立即冲突，因为一个点不能同时属于两侧。重复边不改变结论，但会增加遍历次数。

## 练习

1. 输出二分图的左右两侧点集。
2. 加入自环测试，观察冲突边如何记录。
3. 在确认二分图后，阅读 Kuhn 或 Hopcroft-Karp 匹配算法，区分“可二分”和“最大匹配”两个问题。

## 参考资料

- CP-Algorithms：[Bipartite Graph Check](https://cp-algorithms.com/graph/bipartite-check.html)
- CP-Algorithms：[Kuhn's Algorithm for Maximum Bipartite Matching](https://cp-algorithms.com/graph/kuhn_maximum_bipartite_matching.html)
- cppreference：[std::queue](https://en.cppreference.com/w/cpp/container/queue)

{% endraw %}
