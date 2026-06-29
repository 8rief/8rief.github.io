---
layout: post
title: "DFS 模板：连通块、递归栈和回溯枚举"
date: 2026-06-28 21:43:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用连通块和子集枚举讲清 DFS 的进入/退出时机、visited 和递归栈边界。"
tags: [algorithm, dfs, backtracking, graph, cpp]
---
{% raw %}

> 主题：算法实用基础 / DFS / components / backtracking  
> 本文 lab 已验证：样例图有 3 个连通块，3 个元素的子集枚举结果为 8 个。

DFS 的核心动作是沿一条路径尽量向深处走，走不动时回退。图遍历中，DFS 用 visited 防止重复访问；回溯枚举中，DFS 用递归栈保存当前选择。理解进入节点、处理邻居、退出节点这三个时机，很多模板就会变得清楚。

## 问题模型

第一类问题是图遍历：给定无向图，找出所有连通块。第二类问题是枚举：给定一组元素，枚举所有子集。两者都用递归，但不变量不同：图遍历关心“哪些点已经访问过”，回溯关心“当前路径选择了什么”。

## 核心不变量

![DFS 递归栈和回溯模型](/assets/diagrams/algorithm-dfs-components-backtracking.svg)

图 DFS 的不变量是：进入 `dfs(node)` 时，node 被标记为 visited；函数返回时，从 node 能沿未访问边到达的所有点都已经加入当前连通块。回溯 DFS 的不变量是：递归深度 index 前的选择已经确定，当前位置决定是否选择第 index 个元素。

## 正确性理由

连通块 DFS 从一个未访问点出发，递归访问所有可达邻居。由于每条可达路径都由相邻边组成，递归会沿路径逐步到达每个可达点；visited 防止回到已经处理的点。一次 DFS 收集到的正是该起点所在连通块。遍历所有未访问点后，每个点恰好属于一个连通块。

子集枚举在每个元素上做二选一：不选或选。深度为 n 时，每条递归路径对应一个长度为 n 的二进制选择序列，因此一共得到 `2^n` 个子集，且没有重复。

## 复杂度分析

图 DFS 使用邻接表时，时间复杂度是 `O(V + E)`，空间复杂度是 `O(V)`，其中递归栈最深可能达到 V。子集枚举的时间和输出规模都是 `O(2^n)`，每个输出还可能复制当前路径。枚举问题不能只看代码层数，要先估计输出规模。

## C++ 实现

连通块 DFS：

```cpp
void dfs_component(int node, const vector<vector<int>>& graph,
                   vector<int>& visited, vector<int>& component) {
    visited[node] = 1;
    component.push_back(node);
    for (int next : graph[node]) {
        if (!visited[next]) dfs_component(next, graph, visited, component);
    }
}
```

子集回溯：

```cpp
void backtrack_subsets(const vector<int>& values, int index,
                       vector<int>& current, vector<vector<int>>& out) {
    if (index == static_cast<int>(values.size())) {
        out.push_back(current);
        return;
    }
    backtrack_subsets(values, index + 1, current, out);
    current.push_back(values[index]);
    backtrack_subsets(values, index + 1, current, out);
    current.pop_back();
}
```

`current.pop_back()` 是回溯恢复现场的关键。缺少这一步，后续分支会看到错误状态。

## 测试与边界

lab 输出：

```text
dfs_components=3 subset_count=8
```

边界包括空图、孤立点、自环、重复边、递归深度过大、枚举输出过大。竞赛代码常用递归写 DFS；工程场景或超深图上，可以改成显式栈避免栈溢出。

## 练习

1. 把递归连通块 DFS 改成显式栈版本。
2. 枚举所有大小为 k 的子集，并剪枝跳过不可能达到 k 的分支。
3. 在 DFS 中记录进入时间和退出时间，观察树边和回退时机。

## 参考资料

- CP-Algorithms：[Depth First Search](https://cp-algorithms.com/graph/depth-first-search.html)
- cppreference：[std::vector](https://en.cppreference.com/w/cpp/container/vector)
- cppreference：[Functions](https://en.cppreference.com/w/cpp/language/functions)

{% endraw %}
