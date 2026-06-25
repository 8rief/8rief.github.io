---
layout: post
title: "Li Chao 树：在线维护直线集合的最小值查询"
date: 2026-06-25 15:46:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用直线比较、区间中点和递归替换解释 Li Chao tree，并通过随机直线和暴力最小值对照验证。"
tags: [algorithm, li-chao-tree, convex-hull-trick, dynamic-programming, cplusplus]
---
{% raw %}
> 主题：Li Chao Tree / Convex Hull Trick / 直线最小值 / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

很多 DP 转移可以写成 `dp[i] = min_j(m_j x_i + b_j)`。每个 `j` 提供一条直线，问题就变成动态维护直线集合，并在给定 `x` 上查询最小值。Li Chao 树支持在线加线和在线点查询，对斜率和查询顺序没有单调性要求。

## 学习目标

1. 把一类 DP 转移转成直线最小值查询。
2. 理解节点保存当前区间中点最优线。
3. 实现加入直线和单点查询。
4. 用暴力枚举所有直线验证结果。
5. 区分 Li Chao 树和单调斜率优化。

## 核心模型

![Li Chao 树维护直线下包络](/assets/diagrams/algorithm-li-chao-tree.svg)

在区间内比较新线和当前线。中点更优的线留在当前节点，另一条线只可能在某一侧区间继续产生贡献，于是递归到那一侧。

## C++ 实现片段

```cpp
void add_line(int id, long long l, long long r, Line nw) {
    long long mid = (l + r) / 2;
    Line& cur = nodes_[id].line;
    bool left_better = nw.eval(l) < cur.eval(l);
    bool mid_better = nw.eval(mid) < cur.eval(mid);
    if (mid_better) std::swap(nw, cur);
    if (r - l == 1) return;
    if (left_better != mid_better) add_left_child(nw);
    else add_right_child(nw);
}
```

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
min at x=-5 -> -13
min at x=0 -> -3
min at x=3 -> 2
min at x=10 -> -5
```

测试加入多条直线，并在固定点上与暴力最小值比较。随机测试持续加入 80 条随机直线，查询多个坐标点，确保递归方向和替换逻辑正确。

## 正确性思路

两条直线的差仍是一条直线，在一个区间内最多改变一次符号。比较左端点和中点可以判断失去中点优势的线是否仍可能在左侧胜出；否则它只可能在右侧胜出。查询时沿根到叶路径收集候选线取最小。

## 常见错误

- 坐标域边界不统一；本文使用半开整数域 `[lo, hi)`。
- 递归方向写反，随机暴力对照能快速发现。
- `m*x+b` 溢出；大范围输入需要更宽整数或显式检查。

## 练习

1. 改成维护最大值。
2. 支持只在某个线段区间内加入直线段。
3. 用 Li Chao 树优化一个线性函数 DP。
4. 比较 Li Chao 树和单调 CHT 的约束差异。

## 参考资料

- [cp-algorithms: Convex hull trick and Li Chao tree](https://cp-algorithms.com/geometry/convex_hull_trick.html)
- [cppreference: std::numeric_limits](https://en.cppreference.com/w/cpp/types/numeric_limits)
{% endraw %}
