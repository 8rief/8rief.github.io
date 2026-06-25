---
layout: post
title: "树链剖分：把树上路径拆成少量连续区间"
date: 2026-06-25 15:43:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用重儿子、重链编号、跳链头和线段树解释 HLD，完成树上路径求和并对照朴素路径。"
tags: [algorithm, heavy-light-decomposition, tree, segment-tree, cplusplus]
---
{% raw %}
> 主题：Heavy-Light Decomposition / Tree Path Query / Segment Tree / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

树上路径不天然连续，而线段树擅长处理数组连续区间。树链剖分把树拆成若干重链，并让每条重链在 DFS 序里连续，从而把任意树上路径拆成少量数组区间。

## 学习目标

1. 计算子树大小、父节点、深度和重儿子。
2. 把重链按 DFS 序连续编号。
3. 用线段树维护节点权值。
4. 实现两点路径求和。
5. 用随机树和朴素爬父指针对照结果。

## 核心模型

![树链剖分路径拆分](/assets/diagrams/algorithm-heavy-light-decomposition.svg)

每个节点选择子树最大的儿子作为重儿子。查询时总是先处理链头更深的一侧，累加该链头到当前点的连续区间，然后跳到链头父节点。

## C++ 实现片段

```cpp
long long path_sum(int a, int b) const {
    long long res = 0;
    while (head_[a] != head_[b]) {
        if (depth_[head_[a]] < depth_[head_[b]]) std::swap(a, b);
        res += seg_->query(pos_[head_[a]], pos_[a] + 1);
        a = parent_[head_[a]];
    }
    if (depth_[a] > depth_[b]) std::swap(a, b);
    res += seg_->query(pos_[a], pos_[b] + 1);
    return res;
}
```

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
path_sum(3,7)=19
path_sum(5,6)=16
path_sum(0,7)=16
```

固定树验证手算路径和。随机测试生成多棵树，为节点赋随机值，用朴素方法不断提升深度更大的点，直到两个点相遇，再与 HLD 结果比较。

## 正确性思路

同一条重链的编号连续，链内路径可以转化为线段树区间。跨链时，较深链的链头到当前点这一段一定完全属于目标路径。每跳过一条轻边，所在子树规模至少减半，因此拆分段数为 `O(log n)`。

## 常见错误

- 分解时没有优先递归重儿子，导致重链编号不连续。
- 跳链时处理了链头更浅的一侧。
- 节点权和边权混用；边权版本通常把边权放在较深端点位置。

## 练习

1. 增加单点修改，支持动态节点权路径和。
2. 把路径和改成路径最大值。
3. 利用 DFS 序实现子树查询。
4. 写一个边权版本并对照朴素路径。

## 参考资料

- [cp-algorithms: Heavy-light decomposition](https://cp-algorithms.com/graph/hld.html)
- [cppreference: std::unique_ptr](https://en.cppreference.com/w/cpp/memory/unique_ptr)
{% endraw %}
