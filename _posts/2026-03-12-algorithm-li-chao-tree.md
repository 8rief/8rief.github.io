---
layout: post
title: "Li Chao 树：在线维护直线集合的最小值查询"
date: 2026-03-12 09:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用直线比较、区间中点和递归替换解释 Li Chao tree，并通过随机直线和暴力最小值对照验证。"
tags: [algorithm, li-chao-tree, convex-hull-trick, dynamic-programming, cplusplus]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithms-li-chao-tree/README.md`](/assets/labs/algorithms-li-chao-tree/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：Li Chao Tree / Convex Hull Trick / 直线最小值 / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

很多 DP 转移可以写成 `dp[i] = min_j(m_j x_i + b_j)`。每个 `j` 提供一条直线，问题就变成动态维护直线集合，并在给定 `x` 上查询最小值。Li Chao 树支持在线加线和在线点查询，对斜率和查询顺序没有单调性要求。

暴力做法在每次查询时枚举全部直线，加入 `L` 条线、查询 `Q` 次需要 `O(LQ)`。Li Chao 树利用“两条直线最多相交一次”的结构，把一次加线和一次点查询都限制在坐标树的一条根到叶路径。

## 学习目标

1. 把一类 DP 转移转成直线最小值查询。
2. 理解节点保存当前区间中点最优线。
3. 实现加入直线和单点查询。
4. 用暴力枚举所有直线验证结果。
5. 区分 Li Chao 树和单调斜率优化。

## 核心模型

![Li Chao 树维护直线下包络](/assets/diagrams/algorithm-li-chao-tree.svg)

在区间内比较新线和当前线。中点更优的线留在当前节点，另一条线只可能在某一侧区间继续产生贡献，于是递归到那一侧。

## 为什么要引入中点最优线

设当前线为 `f`、新线为 `g`，差值 `h(x)=g(x)-f(x)` 仍是一次函数。它在区间内至多过零一次。若 `g` 在中点更优，就交换两线，使节点始终保存“中点最优线”；落败线只有可能在左半或右半重新胜出，不需要同时递归两侧。

节点不承诺保存整个区间处处最优的线。真正的不变量是：

```text
当前节点保存中点处更优线；
另一条线若仍可能贡献，只会被递归到唯一一侧；
任意查询点沿根到叶路径的候选最小值等于全局最小值。
```

空节点直接接收新线并停止，这也是动态开点能够节省内存的原因。

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

实际实现还要创建对应子节点并传入新区间：

```cpp
if (left_better != mid_better) {
    if (nodes_[id].left == -1) nodes_[id].left = new_node();
    add_line(nodes_[id].left, l, mid, nw);
} else {
    if (nodes_[id].right == -1) nodes_[id].right = new_node();
    add_line(nodes_[id].right, mid, r, nw);
}
```

`left_better != mid_better` 表示优势在左端与中点之间发生交换，落败线仍可能在左半胜出；否则只需检查右半。

## 实验输出怎样解释

```text
100% tests passed, 0 tests failed out of 1
min at x=-5 -> -13
min at x=0 -> -3
min at x=3 -> 2
min at x=10 -> -5
```

测试加入多条直线，并在固定点上与暴力最小值比较。随机测试持续加入 80 条随机直线，查询多个坐标点，确保递归方向和替换逻辑正确。

固定三条线是 `y=x`、`y=-x+5`、`y=2x-3`。四个查询点可直接手算：

| x | `x` | `-x+5` | `2x-3` | 最小值 |
| ---: | ---: | ---: | ---: | ---: |
| -5 | -5 | 10 | -13 | -13 |
| 0 | 0 | 5 | -3 | -3 |
| 3 | 3 | 2 | 3 | 2 |
| 10 | 10 | -5 | 17 | -5 |

这张表与 demo 输出逐项对应。复跑入口：

```bash
./run_lab.sh
```

随机测试进行 100 轮；每轮依次加入 80 条随机直线，并在 `[-50,50]` 上每隔 5 个坐标与暴力枚举比较。它重点覆盖交换顺序、相交位置和动态子节点创建。

## 正确性思路

两条直线的差仍是一条直线，在一个区间内最多改变一次符号。比较左端点和中点可以判断失去中点优势的线是否仍可能在左侧胜出；否则它只可能在右侧胜出。查询时沿根到叶路径收集候选线取最小。

设整数坐标域长度为 `C=hi-lo`，树高为 `O(log C)`，单次加线和查询都是 `O(log C)`；动态节点最坏随加入线数增长为 `O(L log C)`。复杂度依赖坐标域，不依赖斜率排序。

当前域使用半开区间 `[-10,11)`，覆盖整数 -10 到 10。`query` 没有自行检查越界，调用方必须满足 `lo<=x<hi`。

## 常见错误

- 坐标域边界不统一；本文使用半开整数域 `[lo, hi)`。
- 递归方向写反，随机暴力对照能快速发现。
- `m*x+b` 溢出；大范围输入需要更宽整数或显式检查。
- 把连续实数域与离散整数实现混用；终止条件 `r-l==1` 只适用于当前离散坐标模型。
- 用 `INF` 直线参与乘加；当前实现用 `has` 标记空节点，避免把哨兵当真实候选。

## 练习

1. 改成维护最大值。
2. 支持只在某个线段区间内加入直线段。
3. 用 Li Chao 树优化一个线性函数 DP。
4. 比较 Li Chao 树和单调 CHT 的约束差异。

## 参考资料

- [cp-algorithms: Convex hull trick and Li Chao tree](https://cp-algorithms.com/geometry/convex_hull_trick.html)
- [cppreference: std::numeric_limits](https://en.cppreference.com/w/cpp/types/numeric_limits)
- [cppreference: integer types and width](https://en.cppreference.com/w/cpp/types/integer)
{% endraw %}
