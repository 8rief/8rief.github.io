---
layout: post
title: "BFS 模板：用队列按层找到最短步数"
date: 2026-06-28 21:42:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从网格最短步数讲清 BFS 的队列、visited、层次扩展和路径恢复边界。"
tags: [algorithm, bfs, graph, shortest-path, cpp]
---
{% raw %}

> 主题：算法实用基础 / BFS / unweighted shortest path  
> 本文 lab 已验证：网格从 `S` 到 `G` 的最短步数为 8，恢复路径包含 9 个节点。

BFS 适合解决“每一步代价相同”的最短步数问题。网格走迷宫、单词变换、状态搜索都可以看成无权图：状态是点，一次合法操作是一条边。BFS 用队列按层扩展，因此第一次到达某个状态时，步数就是最短步数。

## 问题模型

输入是一个无权图、起点和终点。输出是从起点到终点的最少边数；如果需要展示方案，还要输出一条最短路径。网格问题中，每个可走格子是点，上下左右移动是边，障碍格不能进入。

## 核心不变量

![BFS 队列和层次不变量](/assets/diagrams/algorithm-bfs-shortest-steps-template.svg)

队列中保存已经发现但尚未扩展的状态。`dist[x]` 一旦被赋值，就表示从起点到 x 的最短步数。队列按距离从小到大弹出；扩展一个点时，只给未访问邻居赋值 `dist[current] + 1`。

## 正确性理由

BFS 从距离 0 的起点开始，先处理所有距离为 1 的点，再处理距离为 2 的点。由于每条边代价都是 1，任何更短路径都必须来自更早层。当某个点第一次被发现时，所有更短路径的上一层已经被处理过；如果没有发现它，说明不存在更短路径。因此第一次写入的距离就是最短距离。

## 复杂度分析

每个点最多入队一次，每条边最多检查常数次。邻接表图的时间复杂度是 `O(V + E)`，空间复杂度是 `O(V)`。网格有 R 行 C 列时，点数是 `RC`，每个点最多 4 个方向，时间和空间都是 `O(RC)`。

## C++ 实现

网格 BFS 的核心结构：

```cpp
queue<pair<int, int>> q;
vector<vector<int>> dist(rows, vector<int>(cols, -1));
vector<vector<pair<int, int>>> parent(rows, vector<pair<int, int>>(cols, {-1, -1}));

dist[start.first][start.second] = 0;
q.push(start);
```

扩展四个方向：

```cpp
for (auto [dr, dc] : dirs) {
    int nr = r + dr, nc = c + dc;
    if (!inside(nr, nc) || grid[nr][nc] == '#' || dist[nr][nc] != -1) continue;
    dist[nr][nc] = dist[r][c] + 1;
    parent[nr][nc] = {r, c};
    q.push({nr, nc});
}
```

`parent` 用来恢复路径。到达终点后，从终点反向沿 parent 走回起点，再反转。

## 测试与边界

lab 的网格输出：

```text
bfs_distance=8 path_nodes=9
```

需要覆盖的边界包括：起点等于终点、终点不可达、障碍围住起点、多个最短路径并存、网格为空或行长度不一致。教学实现假设输入网格合法，工程代码应在边界处做校验。

## 练习

1. 把四方向移动改成八方向移动，重新解释最短步数语义。
2. 在 BFS 中记录每一层有多少节点，输出层次表。
3. 把网格改成状态图，例如 `(位置, 钥匙集合)`，思考 visited 维度如何变化。

## 参考资料

- CP-Algorithms：[Breadth First Search](https://cp-algorithms.com/graph/breadth-first-search.html)
- cppreference：[std::queue](https://en.cppreference.com/w/cpp/container/queue)
- MIT 6.006：[Graph search notes](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/)

{% endraw %}
