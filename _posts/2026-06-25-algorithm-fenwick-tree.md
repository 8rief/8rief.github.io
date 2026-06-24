---
layout: post
title: "Fenwick 树：用 lowbit 维护可更新的前缀和"
date: 2026-06-25 05:35:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从前缀和的在线更新问题引出 Fenwick 树，解释 lowbit 区间、单点加法、前缀求和和随机对照测试。"
tags: [algorithm, fenwick-tree, binary-indexed-tree, range-query, cplusplus]
---
{% raw %}

> 主题：Fenwick 树 / Binary Indexed Tree / 在线前缀和 / C++ 可复现实验  
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含随机单点更新和区间求和对照。

前缀和能 `O(1)` 查询区间和，但数组一旦频繁修改，就要付出重建代价。Fenwick 树解决的是更动态的问题：单点加法和前缀求和都在 `O(log n)` 完成。

它比线段树短很多，却能覆盖大量在线统计问题。理解 Fenwick 树，关键是理解每个树状数组位置保存的是一段由二进制最低位决定的区间和，而非单个元素。

## 学习目标

1. 解释 `lowbit(i) = i & -i` 表示的区间长度。
2. 写出单点 `add` 和前缀 `prefix_sum`。
3. 用前缀差得到 `[l, r)` 区间和。
4. 说明 Fenwick 树和静态前缀和的适用边界。
5. 用随机更新和朴素数组验证实现。

## 核心模型

![Fenwick 树 lowbit 区间](/assets/diagrams/algorithm-fenwick-tree.svg)

Fenwick 树通常内部使用 1-based 下标。`tree[i]` 覆盖的区间长度是 `lowbit(i)`，例如 `i = 8` 覆盖长度 8，`i = 6` 覆盖长度 2。求前缀和时不断去掉最低位，更新时不断加上最低位跳到包含当前点的更大区间。

## C++ 实现

```cpp
class Fenwick {
public:
    explicit Fenwick(int n) : tree_(n + 1, 0) {}

    void add(int index, long long delta) {
        for (int i = index + 1; i < static_cast<int>(tree_.size()); i += i & -i) {
            tree_[i] += delta;
        }
    }

    long long prefix_sum(int count) const {
        long long s = 0;
        for (int i = count; i > 0; i -= i & -i) {
            s += tree_[i];
        }
        return s;
    }

    long long range_sum(int l, int r) const {
        return prefix_sum(r) - prefix_sum(l);
    }
private:
    std::vector<long long> tree_;
};
```

外部接口使用 0-based 下标和半开区间，内部转换成 1-based。这样既贴合 C++ 数组习惯，也保留 Fenwick 树公式的简洁性。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
sum[1,4)=9
after add index 2 += 10, sum[0,3)=16
Fenwick stores disjoint lowbit ranges so prefix sums visit O(log n) nodes
```

随机测试维护一份朴素数组。每一轮随机选择单点加法或区间求和，Fenwick 输出必须和朴素数组逐元素求和一致。这个测试能捕捉 0-based/1-based 转换、半开区间和更新传播方向的错误。

## 正确性思路

`prefix_sum(count)` 把 `[0, count)` 拆成若干个互不重叠的 lowbit 区间。循环中的 `i -= i & -i` 每次取走当前前缀末尾的一段区间，直到覆盖完整前缀。

`add(index, delta)` 需要更新所有包含这个位置的 lowbit 区间。内部下标从 `index + 1` 开始，每次 `i += i & -i` 跳到下一个包含该点的更大管理区间。

## 复杂度

- 单点加法：`O(log n)`。
- 前缀求和：`O(log n)`。
- 区间求和：两次前缀求和，`O(log n)`。
- 空间：`O(n)`。

## 常见错误

**0-based 和 1-based 混乱。** Fenwick 公式依赖正整数下标。建议外部 0-based，内部统一加一。

**`prefix_sum` 参数含义不清。** 本文使用 `count`，表示求 `[0, count)`，这样 `range_sum(l, r)` 自然等于 `prefix_sum(r) - prefix_sum(l)`。

**把 Fenwick 树用于任意区间最值。** Fenwick 最自然支持可逆的前缀聚合，例如和。区间最小值需要额外约束或换线段树。

## 练习

1. 实现“区间加法 + 单点查询”的差分 Fenwick。
2. 实现“区间加法 + 区间求和”的双 Fenwick。
3. 增加 `lower_bound`：找到最小下标使前缀和至少为目标值。
4. 和线段树比较：哪些操作 Fenwick 更简洁，哪些操作线段树更通用？

## 参考资料

- [cp-algorithms: Fenwick Tree](https://cp-algorithms.com/data_structures/fenwick.html)
- [Princeton Algorithms, Part I](https://algs4.cs.princeton.edu/home/)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
{% endraw %}
