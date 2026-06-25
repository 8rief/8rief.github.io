---
layout: post
title: "可持久化线段树：路径复制保存每个版本"
date: 2026-06-25 15:42:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用点更新和区间求和解释路径复制：每次更新只复制根到叶路径，未修改子树被多个版本共享。"
tags: [algorithm, persistent-data-structure, segment-tree, versioning, cplusplus]
---
{% raw %}
> 主题：Persistent Segment Tree / Path Copying / Versioned Range Query / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

普通线段树更新后会覆盖旧状态。可持久化线段树为每个版本保存一个根节点，并保证旧节点不可变。点更新只影响根到叶的一条路径，因此只复制这条路径上的节点，其他子树继续共享。

## 学习目标

1. 理解可持久化结构中的不可变节点和共享子树。
2. 写出点更新时的路径复制逻辑。
3. 保存每个版本的根节点。
4. 验证旧版本不受新版本更新影响。
5. 用朴素数组版本列表对照随机查询。

## 核心模型

![可持久化线段树路径复制](/assets/diagrams/algorithm-persistent-segment-tree.svg)

每次点更新新增 `O(log n)` 个节点。未经过的子树被新旧版本共同引用，所以空间复杂度是 `O(n + V log n)`，其中 `V` 是版本数。

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

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
version0 sum[0,5)=15
version1 set a[2]=10, sum[0,5)=22
version2 set a[0]=-1, sum[0,3)=11
stored versions=3 nodes=15
```

随机测试从随机旧版本派生新版本，并用朴素数组保存每个版本的真实状态。每次随机选择版本和区间，与线段树查询结果对照。

## 正确性思路

一个版本的根节点代表一棵不可变线段树。点更新只改变包含该位置的节点摘要。复制路径上的节点并重算摘要后，新根表示新版本；未复制的子树仍指向旧节点，旧根也仍指向原来的结构，因此历史查询保持正确。

## 常见错误

- 更新时直接修改旧节点，导致历史版本被破坏。
- 只保存最新根节点，无法重新进入旧版本。
- 把每个版本完整深拷贝，空间退化为 `O(Vn)`。

## 练习

1. 把点赋值改成点加法。
2. 查询两个版本之间的区间差分。
3. 实现主席树，回答静态区间第 k 小。
4. 讨论旧版本删除后的节点回收策略。

## 参考资料

- [cp-algorithms: Persistent Segment Tree](https://cp-algorithms.com/data_structures/segment_tree.html#preserving-the-history-of-its-values-persistent-segment-tree)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
{% endraw %}
