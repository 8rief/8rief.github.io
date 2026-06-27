---
layout: page
title: 算法与数据结构
permalink: /algorithms-data-structures/
---

这个栏目专门讲算法与数据结构。文章重点不放在背模板，而是把问题模型、状态定义、不变量、正确性理由、复杂度和可复现实验连起来。每篇文章都应该让读者知道：为什么这个算法能停在正确答案上，哪些输入会触发边界情况，如何用测试确认实现没有偏离模型。

## 写作结构

每篇算法文章默认包含：

1. **问题模型**：输入、输出、约束和目标是什么。
2. **核心不变量**：循环或数据结构在每一步必须保持什么事实。
3. **正确性理由**：为什么不变量能推出最后答案。
4. **复杂度分析**：时间、空间，以及复杂度成立的前提。
5. **C++ 实现**：给出可运行实现，避免只写伪代码。
6. **测试与边界**：固定边界、随机对照、异常输入或可视化 trace。
7. **练习**：用小改动检验理解。


## 建议学习路径

默认文章列表按发布时间倒序展示，不代表学习顺序。建议按下面路线阅读：

| 阶段 | 主题 | 已有文章 |
| --- | --- | --- |
| 1. 边界和线性结构 | 二分、前缀和/差分、双指针、归并、单调栈 | [二分查找](/algorithms-data-structures/2026/06/24/algorithm-binary-search-invariants.html)、[前缀和与差分数组](/algorithms-data-structures/2026/06/25/algorithm-prefix-difference.html)、[双指针与滑动窗口](/algorithms-data-structures/2026/06/25/algorithm-two-pointers-sliding-window.html)、[归并排序与逆序对](/algorithms-data-structures/2026/06/25/algorithm-merge-sort-inversions.html)、[单调栈](/algorithms-data-structures/2026/06/25/algorithm-monotonic-stack.html) |
| 2. 基础数据结构 | 并查集、Fenwick 树、线段树 | [并查集](/algorithms-data-structures/2026/06/24/algorithm-disjoint-set-union.html)、[Fenwick 树](/algorithms-data-structures/2026/06/25/algorithm-fenwick-tree.html)、[线段树懒标记](/algorithms-data-structures/2026/06/25/algorithm-segment-tree-lazy.html) |
| 3. 图算法 | 遍历、最短路、生成树、最大流 | [图遍历和拓扑排序](/algorithms-data-structures/2026/06/25/algorithm-graph-traversal-toposort.html)、[Dijkstra](/algorithms-data-structures/2026/06/24/algorithm-dijkstra-priority-queue.html)、[Bellman-Ford](/algorithms-data-structures/2026/06/25/algorithm-bellman-ford-negative-cycle.html)、[最小生成树](/algorithms-data-structures/2026/06/25/algorithm-mst-kruskal-prim.html)、[Dinic 最大流](/algorithms-data-structures/2026/06/25/algorithm-dinic-max-flow.html) |
| 4. 字符串 | KMP、Trie/Aho-Corasick、后缀数组 | [KMP](/algorithms-data-structures/2026/06/25/algorithm-kmp-prefix-function.html)、[Trie 和 Aho-Corasick](/algorithms-data-structures/2026/06/25/algorithm-trie-aho-corasick.html)、[后缀数组和 LCP](/algorithms-data-structures/2026/06/25/algorithm-suffix-array-lcp.html) |
| 5. 树上和持久化结构 | LCA、树链剖分、可持久化线段树、Li Chao 树 | [倍增 LCA](/algorithms-data-structures/2026/06/25/algorithm-binary-lifting-lca.html)、[树链剖分](/algorithms-data-structures/2026/06/25/algorithm-heavy-light-decomposition.html)、[可持久化线段树](/algorithms-data-structures/2026/06/25/algorithm-persistent-segment-tree.html)、[Li Chao 树](/algorithms-data-structures/2026/06/25/algorithm-li-chao-tree.html) |
| 6. 数学、随机和博弈 | 数论、计算几何、NTT、摊还、随机化、SG | [数论工具箱](/algorithms-data-structures/2026/06/25/algorithm-number-theory-toolkit.html)、[计算几何基础](/algorithms-data-structures/2026/06/25/algorithm-computational-geometry-basics.html)、[NTT 卷积](/algorithms-data-structures/2026/06/25/algorithm-ntt-convolution.html)、[摊还分析](/algorithms-data-structures/2026/06/25/algorithm-amortized-dynamic-array.html)、[随机化 Quickselect](/algorithms-data-structures/2026/06/25/algorithm-randomized-quickselect.html)、[Sprague-Grundy 定理](/algorithms-data-structures/2026/06/25/algorithm-sprague-grundy-games.html) |

后续补算法时优先补缺口：堆、哈希表、优先队列模型、基础 DP 题型拆分、BFS/DFS 模板化练习、二分图、最短路路径恢复和常见复杂度陷阱。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "algorithms-data-structures" %}
{% if posts.size == 0 %}
暂时没有文章。后续会从二分查找、并查集、最短路等基础主题开始。
{% else %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}
