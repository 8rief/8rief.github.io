---
layout: post
title: "BFS 模板：用队列按层找到最短步数"
date: 2026-03-03 18:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从网格最短步数讲清 BFS 的队列、visited、层次扩展和路径恢复边界。"
tags: [algorithm, bfs, graph, shortest-path, cpp]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithm-practical-foundations/README.md`](/assets/labs/algorithm-practical-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：算法实用基础 / BFS / unweighted shortest path  
> 本文 lab 已验证：网格从 `S` 到 `G` 的最短步数为 8，恢复路径包含 9 个节点。

BFS 适合解决“每一步代价相同”的最短步数问题。网格走迷宫、单词变换、状态搜索都可以看成无权图：状态是点，一次合法操作是一条边。BFS 用队列按层扩展，因此第一次到达某个状态时，步数就是最短步数。

若用普通 DFS 找最短步数，需要枚举或反复修正很多路径；BFS 的队列顺序直接维护距离层次，让第一次发现成为可证明的最短结果。

## 问题模型

输入是一个无权图、起点和终点。输出是从起点到终点的最少边数；如果需要展示方案，还要输出一条最短路径。网格问题中，每个可走格子是点，上下左右移动是边，障碍格不能进入。

## 为什么要引入队列和 visited

队列保证先发现的较小距离层先扩展。visited 在本实现中由 `dist!=-1` 表示，并在**入队时**写入：

```text
弹出距离 d 的点
  -> 所有未访问邻居写入 d+1
  -> 立即标记并入队
```

若等到出队才标记，同一节点可能被多个前驱重复加入队列，既浪费空间，也让 parent 来源变得不清楚。

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

## 固定网格的层次与路径

lab 使用：

```text
S..#.
.#.#.
.#...
.###.
....G
```

一条最短路径是：

```text
(0,0) -> (1,0) -> (2,0) -> (3,0) -> (4,0)
      -> (4,1) -> (4,2) -> (4,3) -> (4,4)
```

它包含 9 个节点、8 条边，所以 `path_nodes=distance+1`。parent 记录的是节点，不是移动次数。

## 测试输出怎样解释

lab 的网格输出：

```text
bfs_distance=8 path_nodes=9
```

复跑：

```bash
./run_lab.sh
```

本文相关的四个断言分别检查距离 8、路径节点数 9、首节点为起点、末节点为终点。到达 goal 时循环在 goal 出队后停止，此时所有更短层已经处理完，距离已经最终确定。

需要覆盖的边界包括：起点等于终点、终点不可达、障碍围住起点、多个最短路径并存、网格为空或行长度不一致。教学实现假设输入网格合法，工程代码应在边界处做校验。

## 适用边界

- 所有边权相同：普通 BFS；
- 边权只有 0 和 1：0-1 BFS；
- 任意非负边权：Dijkstra；
- 含负权：需要其他算法。

把带权问题强行按边数做 BFS，得到的是“最少边数”，不一定是“最小总成本”。

## 常见错误

1. 在出队时才标记 visited，产生大量重复入队。
2. 只保存距离，没有 parent，却在最后试图恢复路径。
3. 不可达时仍沿 `(-1,-1)` parent 访问数组。
4. 多个最短路径并存时，把某一条固定路径顺序当唯一答案。
5. 未验证空网格、非矩形网格、越界或障碍起终点。

## 练习

1. 把四方向移动改成八方向移动，重新解释最短步数语义。
2. 在 BFS 中记录每一层有多少节点，输出层次表。
3. 把网格改成状态图，例如 `(位置, 钥匙集合)`，思考 visited 维度如何变化。
4. 验证恢复路径中每对相邻坐标确实相邻且都不是障碍。

## 参考资料

- CP-Algorithms：[Breadth First Search](https://cp-algorithms.com/graph/breadth-first-search.html)
- cppreference：[std::queue](https://en.cppreference.com/w/cpp/container/queue)
- MIT 6.006：[Graph search notes](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/)

{% endraw %}
