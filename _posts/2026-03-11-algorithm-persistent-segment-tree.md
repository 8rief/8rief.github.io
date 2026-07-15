---
layout: post
title: "可持久化线段树：路径复制保存每个版本"
date: 2026-03-11 18:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用点更新和区间求和解释路径复制：每次更新只复制根到叶路径，未修改子树被多个版本共享。"
tags: [algorithm, persistent-data-structure, segment-tree, versioning, cplusplus]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithms-persistent-segment-tree/README.md`](/assets/labs/algorithms-persistent-segment-tree/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：Persistent Segment Tree / Path Copying / Versioned Range Query / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

普通线段树更新后会覆盖旧状态。可持久化线段树为每个版本保存一个根节点，并保证旧节点不可变。点更新只影响根到叶的一条路径，因此只复制这条路径上的节点，其他子树继续共享。

如果把每个历史数组完整复制一份，`V` 个版本需要 `O(Vn)` 空间；如果只保留最新数组，又无法查询历史状态。路径复制利用“单点更新只触及 `O(log n)` 个摘要节点”，在历史可查询和空间之间取得更好的结构化折中。

## 学习目标

1. 理解可持久化结构中的不可变节点和共享子树。
2. 写出点更新时的路径复制逻辑。
3. 保存每个版本的根节点。
4. 验证旧版本不受新版本更新影响。
5. 用朴素数组版本列表对照随机查询。

## 核心模型

![可持久化线段树路径复制](/assets/diagrams/algorithm-persistent-segment-tree.svg)

每次点更新新增 `O(log n)` 个节点。未经过的子树被新旧版本共同引用，所以空间复杂度是 `O(n + V log n)`，其中 `V` 是版本数。

## 为什么要引入路径复制

每个版本只保存一个根索引。更新从旧根开始，把路径上节点复制到 `Node cur`，只修改副本的一个子指针，再把新节点追加到 `nodes_`：

```text
old root ── old left subtree
    │      └ old right subtree
    │
new root ── copied path ── new leaf
    └────── shared untouched subtree
```

旧根和旧节点永远不被原地改写，所以它们仍描述原版本。新版本可以从任意旧版本分支，版本关系形成树，而非只能线性前进。

## C++ 实现片段

```cpp
int update_node(int id, int l, int r, int index, int value) {
    Node cur = nodes_[id];
    if (r - l == 1) {
        cur.sum = value;
        return new_node(cur);
    }
    int m = (l + r) / 2;
    if (index < m) cur.left = update_node(cur.left, l, m, index, value);
    else cur.right = update_node(cur.right, m, r, index, value);
    cur.sum = nodes_[cur.left].sum + nodes_[cur.right].sum;
    return new_node(cur);
}
```

关键语句 `Node cur = nodes_[id]` 复制当前节点。递归只返回一个新孩子索引，另一侧索引保留不变，因此整棵未修改子树被共享。父节点 sum 根据两个孩子重新计算后再追加：

```cpp
cur.sum = nodes_[cur.left].sum + nodes_[cur.right].sum;
return new_node(cur);
```

若把 `Node& cur = nodes_[id]` 写成引用并原地修改，所有引用该节点的历史版本都会被污染。

## 实验输出怎样解释

```text
100% tests passed, 0 tests failed out of 1
version0 sum[0,5)=15
version1 set a[2]=10, sum[0,5)=22
version2 set a[0]=-1, sum[0,3)=11
stored versions=3 nodes=15
```

随机测试从随机旧版本派生新版本，并用朴素数组保存每个版本的真实状态。每次随机选择版本和区间，与线段树查询结果对照。

固定数组初始为 `[1,2,3,4,5]`：

```text
v0: [ 1,2, 3,4,5]  sum[0,5)=15
v1: [ 1,2,10,4,5]  sum[0,5)=22
v2: [-1,2,10,4,5]  sum[0,3)=11
```

`v1` 从 `v0` 修改下标 2，`v2` 从 `v1` 修改下标 0；查询 `v0` 的 `[0,3)` 仍为 6，直接验证历史未被覆盖。

## 为什么节点数是 15

5 个叶子的初始满二叉分解共有 `2n-1=9` 个节点。当前递归区间为：

```text
[0,5) -> [0,2) + [2,5)
```

更新下标 2 会复制 `[0,5)`、`[2,5)`、`[2,3)` 三个节点，节点数从 9 变 12；更新下标 0 再复制三层，最终为 15。实际每次新增节点数由树高决定，数量级为 `O(log n)`。

复跑：

```bash
./run_lab.sh
```

随机测试先生成长度 30 的数组，再从随机历史版本派生 200 个新版本；每轮做 5 次随机区间查询，与完整数组副本的朴素和比较，约覆盖 1000 次历史查询。

## 正确性思路

一个版本的根节点代表一棵不可变线段树。点更新只改变包含该位置的节点摘要。复制路径上的节点并重算摘要后，新根表示新版本；未复制的子树仍指向旧节点，旧根也仍指向原来的结构，因此历史查询保持正确。

初建为 `O(n)`，点更新为 `O(log n)` 时间和新增空间，区间查询为 `O(log n)`，保存根索引为每版本 `O(1)`。总空间为初始 `O(n)` 加所有更新路径。

## 常见错误

- 更新时直接修改旧节点，导致历史版本被破坏。
- 只保存最新根节点，无法重新进入旧版本。
- 把每个版本完整深拷贝，空间退化为 `O(Vn)`。
- 把“可持久化”理解成磁盘持久化；这里指旧版本的数据结构仍可访问，进程退出后不会自动保存。
- 忽略输入前置条件；当前教学实现用 `.at()` 检查版本号，但假设 `0<=index<n` 且查询区间合法。

## 练习

1. 把点赋值改成点加法。
2. 查询两个版本之间的区间差分。
3. 实现主席树，回答静态区间第 k 小。
4. 讨论旧版本删除后的节点回收策略。

## 参考资料

- [cp-algorithms: Persistent Segment Tree](https://cp-algorithms.com/data_structures/segment_tree.html#preserving-the-history-of-its-values-persistent-segment-tree)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
- [cppreference: std::vector::reserve](https://en.cppreference.com/w/cpp/container/vector/reserve)
{% endraw %}
