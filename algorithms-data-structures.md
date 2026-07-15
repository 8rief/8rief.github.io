---
layout: page
title: 算法与数据结构
permalink: /algorithms-data-structures/
---

这个栏目专门讲算法与数据结构。文章把问题模型、状态定义、不变量、正确性理由、复杂度和可复现实验连起来。每篇文章都说明算法为什么能停在正确答案上、哪些输入会触发边界情况、如何用测试确认实现没有偏离模型。

## 学一篇算法文章时要完成什么

学习每篇文章时，依次完成下面七件事：

1. **问题模型**：输入、输出、约束和目标是什么。
2. **核心不变量**：循环或数据结构在每一步必须保持什么事实。
3. **正确性理由**：为什么不变量能推出最后答案。
4. **复杂度分析**：时间、空间，以及复杂度成立的前提。
5. **C++ 实现**：给出可运行实现，避免只写伪代码。
6. **测试与边界**：固定边界、随机对照、异常输入或可视化 trace。
7. **练习**：用小改动检验理解。


## 建议学习路径

下面按算法能力组织学习路线：

| 阶段 | 主题 | 已有文章 |
| --- | --- | --- |
| 1. 边界和线性结构 | 二分、前缀和/差分、双指针、归并、单调栈 | [二分查找](/algorithms-data-structures/2026/02/26/algorithm-binary-search-invariants.html)、[前缀和与差分数组](/algorithms-data-structures/2026/02/27/algorithm-prefix-difference.html)、[双指针与滑动窗口](/algorithms-data-structures/2026/02/27/algorithm-two-pointers-sliding-window.html)、[归并排序与逆序对](/algorithms-data-structures/2026/02/28/algorithm-merge-sort-inversions.html)、[单调栈](/algorithms-data-structures/2026/02/28/algorithm-monotonic-stack.html) |
| 2. 基础数据结构 | 堆/优先队列、哈希表、并查集、Fenwick 树、线段树 | [堆和优先队列](/algorithms-data-structures/2026/03/01/algorithm-heap-priority-queue-topk.html)、[哈希表和哈希集合](/algorithms-data-structures/2026/03/01/algorithm-hash-table-frequency-lookup.html)、[并查集](/algorithms-data-structures/2026/03/02/algorithm-disjoint-set-union.html)、[Fenwick 树](/algorithms-data-structures/2026/03/02/algorithm-fenwick-tree.html)、[线段树懒标记](/algorithms-data-structures/2026/03/03/algorithm-segment-tree-lazy.html) |
| 3. 图算法 | BFS、DFS、二分图、最短路、生成树、最大流 | [BFS 模板](/algorithms-data-structures/2026/03/03/algorithm-bfs-shortest-steps-template.html)、[DFS 模板](/algorithms-data-structures/2026/03/04/algorithm-dfs-components-backtracking.html)、[二分图染色](/algorithms-data-structures/2026/03/04/algorithm-bipartite-coloring-model.html)、[Dijkstra](/algorithms-data-structures/2026/03/05/algorithm-dijkstra-priority-queue.html)、[最短路路径恢复](/algorithms-data-structures/2026/03/05/algorithm-shortest-path-restore-dijkstra.html)、[Bellman-Ford](/algorithms-data-structures/2026/03/06/algorithm-bellman-ford-negative-cycle.html)、[最小生成树](/algorithms-data-structures/2026/03/06/algorithm-mst-kruskal-prim.html)、[Dinic 最大流](/algorithms-data-structures/2026/03/07/algorithm-dinic-max-flow.html) |
| 4. 动态规划和复杂度 | 基础 DP、背包、复杂度陷阱、边界测试 | [动态规划入门](/algorithms-data-structures/2026/03/07/algorithm-dynamic-programming-core.html)、[基础 DP 题型](/algorithms-data-structures/2026/03/08/algorithm-basic-dp-patterns.html)、[复杂度陷阱和边界测试](/algorithms-data-structures/2026/03/08/algorithm-complexity-traps-boundary-tests.html) |
| 5. 字符串 | KMP、Trie/Aho-Corasick、后缀数组 | [KMP](/algorithms-data-structures/2026/03/09/algorithm-kmp-prefix-function.html)、[Trie 和 Aho-Corasick](/algorithms-data-structures/2026/03/09/algorithm-trie-aho-corasick.html)、[后缀数组和 LCP](/algorithms-data-structures/2026/03/10/algorithm-suffix-array-lcp.html) |
| 6. 树上和持久化结构 | LCA、树链剖分、可持久化线段树、Li Chao 树 | [倍增 LCA](/algorithms-data-structures/2026/03/10/algorithm-binary-lifting-lca.html)、[树链剖分](/algorithms-data-structures/2026/03/11/algorithm-heavy-light-decomposition.html)、[可持久化线段树](/algorithms-data-structures/2026/03/11/algorithm-persistent-segment-tree.html)、[Li Chao 树](/algorithms-data-structures/2026/03/12/algorithm-li-chao-tree.html) |
| 7. 数学、随机和博弈 | 数论、计算几何、NTT、摊还、随机化、SG | [数论工具箱](/algorithms-data-structures/2026/03/12/algorithm-number-theory-toolkit.html)、[计算几何基础](/algorithms-data-structures/2026/03/13/algorithm-computational-geometry-basics.html)、[NTT 卷积](/algorithms-data-structures/2026/03/13/algorithm-ntt-convolution.html)、[摊还分析](/algorithms-data-structures/2026/03/14/algorithm-amortized-dynamic-array.html)、[随机化 Quickselect](/algorithms-data-structures/2026/03/14/algorithm-randomized-quickselect.html)、[Sprague-Grundy 定理](/algorithms-data-structures/2026/03/15/algorithm-sprague-grundy-games.html) |

每个阶段完成后确认三件事：能说清核心不变量，能解释复杂度为什么成立，能用边界测试或随机对拍发现实现错误。做到这三点，再进入下一阶段。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "algorithms-data-structures" %}
{% if posts.size == 0 %}
当前没有匹配到本栏目文章。请先回到[栏目地图](/columns/)或[全部文章](/posts/)确认导航入口。
{% else %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}
