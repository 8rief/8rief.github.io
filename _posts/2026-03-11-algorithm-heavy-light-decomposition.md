---
layout: post
title: "树链剖分：把树上路径拆成少量连续区间"
date: 2026-03-11 09:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用重儿子、重链编号、跳链头和线段树解释 HLD，完成树上路径求和并对照朴素路径。"
tags: [algorithm, heavy-light-decomposition, tree, segment-tree, cplusplus]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithms-heavy-light-decomposition/README.md`](/assets/labs/algorithms-heavy-light-decomposition/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：Heavy-Light Decomposition / Tree Path Query / Segment Tree / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

树上路径不天然连续，而线段树擅长处理数组连续区间。树链剖分把树拆成若干重链，并让每条重链在 DFS 序里连续，从而把任意树上路径拆成少量数组区间。

如果每次路径查询都沿父指针逐点走，链状树上的一次查询可能访问 `O(n)` 个节点。HLD 的目标是把“树上不连续路径”转成少量数组区间，让已有的区间数据结构复用到树上。

## 学习目标

1. 计算子树大小、父节点、深度和重儿子。
2. 把重链按 DFS 序连续编号。
3. 用线段树维护节点权值。
4. 实现两点路径求和。
5. 用随机树和朴素爬父指针对照结果。

## 核心模型

![树链剖分路径拆分](/assets/diagrams/algorithm-heavy-light-decomposition.svg)

每个节点选择子树最大的儿子作为重儿子。查询时总是先处理链头更深的一侧，累加该链头到当前点的连续区间，然后跳到链头父节点。

## 为什么要引入重边和轻边

对节点 `u`，选择子树大小最大的儿子作为重儿子，其余父子边为轻边。若 `v` 是 `u` 的轻儿子，则必有：

```text
size[v] <= (size[u]-1)/2 < size[u]/2
```

否则 `v` 会比被选中的重儿子更大。沿根到叶路径每经过一条轻边，当前子树规模至少减半，因此轻边数量至多 `O(log n)`。任意两点路径也只会跨过 `O(log n)` 条轻边，进而拆成 `O(log n)` 段重链。

## 两遍 DFS 分别维护什么

第一遍 `dfs_size` 计算 `parent`、`depth`、`size` 和 `heavy`：

```cpp
size_[u] = 1;
for (int v : g_[u]) {
    if (v == parent_[u]) continue;
    depth_[v] = depth_[u] + 1;
    int child_size = dfs_size(v, u);
    size_[u] += child_size;
    if (child_size > best) {
        best = child_size;
        heavy_[u] = v;
    }
}
```

第二遍 `decompose` 先递归重儿子，让整条重链获得连续 `pos`；每个轻儿子开启以自己为头的新链。

固定树的一个合法编号为：

```text
node: 0 1 4 7 | 3 | 2 5 | 6
pos:  0 1 2 3 | 4 | 5 6 | 7
head: 0 0 0 0 | 3 | 2 2 | 6
```

竖线分隔重链。若重儿子有并列，具体编号可因邻接表顺序变化，但“每条重链连续”和查询结果不能变化。

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

## 实验输出怎样解释

```text
100% tests passed, 0 tests failed out of 1
path_sum(3,7)=19
path_sum(5,6)=16
path_sum(0,7)=16
```

固定树验证手算路径和。随机测试生成多棵树，为节点赋随机值，用朴素方法不断提升深度更大的点，直到两个点相遇，再与 HLD 结果比较。

以 `path_sum(3,7)` 为例，真实路径是 `3 -> 1 -> 4 -> 7`，节点权为 `4+2+5+8=19`。查询状态如下：

```text
head[3]=3, head[7]=0
先取链 [3..3]，贡献 4，3 跳到 parent[3]=1
此时 1 和 7 同链，取连续区间 [pos[1],pos[7]]，贡献 15
总和 19
```

`pos[a] + 1` 作为半开右端点，使线段树区间 `[pos[head], pos[a]+1)` 包含两个端点。

## 怎样复跑和读测试

```bash
./run_lab.sh
```

脚本使用 GCC 13.3.0、CMake 3.28.3 和 Ninja 1.11.1 构建，随后运行 CTest 和 demo。当前测试除了三条固定路径，还生成 80 棵树、每棵比较 200 次随机路径，共 16000 次 HLD/朴素结果对照。

## 正确性思路

同一条重链的编号连续，链内路径可以转化为线段树区间。跨链时，较深链的链头到当前点这一段一定完全属于目标路径。每跳过一条轻边，所在子树规模至少减半，因此拆分段数为 `O(log n)`。

处理较深链头还有一个关键作用：该链段不会越过两点的 LCA。把它累加后跳到 `parent[head]`，问题规模严格向根收缩；当两个点进入同一重链，只需一次区间查询。

预处理为 `O(n)`。当前每段调用一次 `O(log n)` 线段树查询，所以路径查询为 `O(log² n)`；单点更新为 `O(log n)`。若查询运算允许链内前缀缓存，可在某些静态场景进一步降到 `O(log n)`。

## 常见错误

- 分解时没有优先递归重儿子，导致重链编号不连续。
- 跳链时处理了链头更浅的一侧。
- 节点权和边权混用；边权版本通常把边权放在较深端点位置。
- 忘记空树、越界节点或非连通输入的前置条件；当前教学实现假设输入是一棵以 0 为根的非空树。

## 练习

1. 增加单点修改，支持动态节点权路径和。
2. 把路径和改成路径最大值。
3. 利用 DFS 序实现子树查询。
4. 写一个边权版本并对照朴素路径。

## 参考资料

- [cp-algorithms: Heavy-light decomposition](https://cp-algorithms.com/graph/hld.html)
- [USACO Guide: Heavy-Light Decomposition](https://usaco.guide/plat/hld)
- [cppreference: std::unique_ptr](https://en.cppreference.com/w/cpp/memory/unique_ptr)
{% endraw %}
