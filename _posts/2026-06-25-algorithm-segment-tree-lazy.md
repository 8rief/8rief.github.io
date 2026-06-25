---
layout: post
title: "线段树懒标记：区间加法和区间求和"
date: 2026-06-25 14:10:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用区间 sum 和 lazy add 解释线段树懒传播，给出 range add、range sum、随机朴素数组对照和常见边界错误。"
tags: [algorithm, segment-tree, lazy-propagation, range-query, cplusplus]
---
{% raw %}
> 主题：Segment Tree / Lazy Propagation / 区间加法 / 区间求和 / C++ 可复现实验
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含固定区间更新和随机朴素数组对照。

Fenwick 树适合前缀型可逆聚合。线段树更通用：它把数组递归拆成区间树，每个节点保存一个区间的摘要。懒标记解决的是区间更新的重复下钻问题。

以“区间加法 + 区间求和”为例，如果一个更新区间完全覆盖当前节点，直接修改节点的 `sum`，并把增量记到 `lazy`。只有后续查询或更新需要访问子节点时，才把标记下传。

## 学习目标

1. 理解节点区间 `[l, r)`、左右子区间和父节点摘要。
2. 写出 `apply`、`push`、`range_add`、`range_sum` 四个核心函数。
3. 说明懒标记为何能保持查询正确。
4. 用朴素数组做随机对照测试。
5. 识别闭区间、半开区间和节点长度相关错误。

## 核心模型

![线段树懒标记模型](/assets/diagrams/algorithm-segment-tree-lazy.svg)

一个节点保存两类信息：`sum` 是当前区间真实和；`lazy` 是还没有下传给子节点的统一增量。只要访问子节点前执行 `push`，父子之间的信息就会重新一致。

## C++ 实现片段

```cpp
class SegmentTree {
    struct Node { long long sum = 0, lazy = 0; };
    int n;
    vector<Node> tree;

    void apply(int p, int l, int r, long long delta) {
        tree[p].sum += delta * (r - l);
        tree[p].lazy += delta;
    }

    void push(int p, int l, int r) {
        if (tree[p].lazy == 0 || r - l == 1) return;
        int m = (l + r) / 2;
        apply(p * 2, l, m, tree[p].lazy);
        apply(p * 2 + 1, m, r, tree[p].lazy);
        tree[p].lazy = 0;
    }

    void range_add(int p, int l, int r, int ql, int qr, long long delta) {
        if (qr <= l || r <= ql) return;
        if (ql <= l && r <= qr) return apply(p, l, r, delta);
        push(p, l, r);
        int m = (l + r) / 2;
        range_add(p * 2, l, m, ql, qr, delta);
        range_add(p * 2 + 1, m, r, ql, qr, delta);
        tree[p].sum = tree[p * 2].sum + tree[p * 2 + 1].sum;
    }
};
```

本文外部接口统一使用半开区间 `[l, r)`，这样左右子区间自然写成 `[l, m)` 和 `[m, r)`，也方便与 C++ 标准库区间习惯保持一致。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
after add [1,4)+=10, sum[0,3)=26
sum[3,5)=19
```

随机测试维护一份朴素数组。每轮随机执行区间加法或区间求和，线段树结果必须与逐元素更新和求和一致。这个测试覆盖了局部覆盖、完全覆盖、无交集、单点长度区间和多次叠加的组合。

## 正确性思路

`apply` 保证一个节点区间整体加 `delta` 后，节点 `sum` 立刻正确。`lazy` 记录“如果未来访问子节点，它们也需要加这个 delta”。

递归查询或部分更新要进入子节点时，先执行 `push`，把父节点的待处理增量分发给左右子节点。此后子节点摘要正确，递归返回时再用左右子节点重算父节点 `sum`。因此每个递归出口都维护了“节点摘要等于区间真实和”的不变量。

## 复杂度

- 区间加法：`O(log n)` 个区间节点被完全覆盖或沿边界递归。
- 区间求和：`O(log n)` 个区间节点组合结果。
- 空间：`O(n)`，常见实现分配 `4n` 个节点。

## 常见错误

**忘记乘以区间长度。** 区间整体加 `delta` 时，`sum` 增加的是 `delta * (r - l)`。

**进入子节点前没有 push。** 子节点会缺少父节点积累的更新，后续查询得到旧值。

**半开区间和闭区间混写。** 建议在函数签名里始终使用 `[l, r)`，并用 `qr <= l || r <= ql` 表示无交集。

## 练习

1. 增加区间赋值操作，思考赋值标记和加法标记的优先级。
2. 改成维护区间最大值和最大值出现次数。
3. 实现动态开点线段树，支持很大的坐标范围。
4. 用线段树完成扫描线面积并集问题。

## 参考资料

- [cp-algorithms: Segment Tree](https://cp-algorithms.com/data_structures/segment_tree.html)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
{% endraw %}
