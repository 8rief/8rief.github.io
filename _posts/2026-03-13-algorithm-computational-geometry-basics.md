---
layout: post
title: "计算几何基础：方向、线段相交和凸包"
date: 2026-03-13 09:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用二维向量叉积统一解释方向判断、线段相交和 Andrew 凸包，并给出整数坐标下的边界处理。"
tags: [algorithm, computational-geometry, convex-hull, geometry, cplusplus]
---
{% raw %}
> 主题：Computational Geometry / orientation / segment intersection / convex hull / C++ 可复现实验
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含方向判断、线段相交、共线边界和凸包结果验证。

计算几何的入门难点经常来自边界条件：共线、端点相交、重复点、凸包上要不要保留中间点。处理这些问题前，先要把方向判断写稳。

二维向量叉积 `cross(b-a, c-a)` 的符号表示从 `a->b` 转到 `a->c` 的方向：正数为逆时针，负数为顺时针，0 为共线。线段相交和凸包维护都可以建立在这个符号判断之上。

## 为什么需要先稳定谓词

几何算法的高层逻辑经常很短，错误却集中在最底层谓词。方向判断若在共线、端点和大坐标上不稳定，线段相交会漏掉接触点，凸包会把边界点错误弹出或保留。

在整数坐标问题中，优先用整数叉积。它给出精确符号，不需要设置浮点 `eps`。只有涉及距离、角度、圆和非整数交点时，再引入浮点数和误差策略。

## 学习目标

1. 用整数叉积实现 orientation，避免小规模整数输入中的浮点误差。
2. 写出包含端点和共线情况的线段相交判断。
3. 实现 Andrew monotonic chain 凸包。
4. 解释凸包中共线点保留策略。
5. 用固定样例验证边界行为。

## 核心模型

![计算几何基础链条](/assets/diagrams/algorithm-computational-geometry-basics.svg)

方向判断是底层谓词。线段相交使用两组方向和包围盒检查；凸包则按排序后的点序维护只向同一方向转的边界链。

两个基本方向样例：

```text
cross((0,0),(2,0),(1,1))  = 2  > 0，点在有向边左侧
cross((0,0),(2,0),(1,-1)) = -2 < 0，点在有向边右侧
```

线段 `(0,0)-(4,4)` 与 `(0,4)-(4,0)` 的四个方向值为 `16,-16,-16,16`，两组端点分别位于对方直线两侧，所以严格相交。若某个方向值为 0，则退回 `on_segment` 检查它是否真的落在线段包围盒内。

## C++ 实现片段

```cpp
struct Point { long long x, y; };

long long cross(Point a, Point b, Point c) {
    long long x1 = b.x - a.x, y1 = b.y - a.y;
    long long x2 = c.x - a.x, y2 = c.y - a.y;
    return x1 * y2 - y1 * x2;
}

bool on_segment(Point a, Point b, Point p) {
    return cross(a, b, p) == 0
        && min(a.x, b.x) <= p.x && p.x <= max(a.x, b.x)
        && min(a.y, b.y) <= p.y && p.y <= max(a.y, b.y);
}

bool segments_intersect(Point a, Point b, Point c, Point d) {
    long long c1 = cross(a, b, c), c2 = cross(a, b, d);
    long long c3 = cross(c, d, a), c4 = cross(c, d, b);
    if (((c1 > 0 && c2 < 0) || (c1 < 0 && c2 > 0)) &&
        ((c3 > 0 && c4 < 0) || (c3 < 0 && c4 > 0))) return true;
    return on_segment(a, b, c) || on_segment(a, b, d)
        || on_segment(c, d, a) || on_segment(c, d, b);
}
```

Andrew 凸包先按 `(x,y)` 排序并去重，再维护下凸壳和上凸壳。本文实现使用 `cross <= 0` 弹出末尾点，因此边界上的共线中间点会被移除，只保留端点。

固定点集去重排序后，内部点 `(1,1)` 和边界中间点 `(1,0)` 都不会留在最终凸包里；输出为：

```text
(0,0) -> (2,0) -> (2,2) -> (0,2)
```

这是逆时针顺序的严格顶点集合。若应用场景要保留边上的采样点，弹出条件和后处理都要改变。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
convex hull: (0,0) (2,0) (2,2) (0,2)
segments intersect=true
```

凸包样例包含正方形内部点、边界点和重复点，输出四个角。线段相交样例覆盖真正交叉；测试里还包含共线重叠、共线分离、全体共线点凸包只保留两端点，保证端点、包围盒和共线策略都被检查。

## 正确性思路

两条线段严格相交时，线段 `cd` 的两个端点位于有向直线 `ab` 两侧，线段 `ab` 的两个端点也位于有向直线 `cd` 两侧。共线或端点接触时，两侧判断会退化到 0，因此需要额外检查点是否落在线段包围盒内。

凸包维护时，排序后的点从左到右加入。下凸壳中如果最后两个点与新点形成非左转，末尾点无法成为严格凸边界点，可以弹出。上凸壳同理。两条链合并后得到逆时针凸包。

## 复杂度

- 方向判断和线段相交：`O(1)`。
- Andrew 凸包：排序 `O(n log n)`，维护栈总计 `O(n)`。
- 空间：凸包和排序数组 `O(n)`。

维护栈虽然有 while 循环，但每个点最多入栈一次、被弹出一次，因此排序后的扫描部分是线性的。

## 输入和数值边界

- `long long` 能覆盖常见 `1e9` 级坐标乘积，但更大坐标可能让叉积溢出；可改用 `__int128` 计算叉积。
- 当前凸包会删除重复点，并删除共线中间点。
- `inside_or_on_convex` 在实验里只用于验证凸包结果；真实点包含测试要单独处理退化凸包。
- 浮点几何不能直接复用 `cross==0`，需要误差阈值和一致的比较策略。

## 常见错误

**用 int 存叉积。** 坐标达到 `1e9` 时，乘积会超过 32 位范围。本文使用 `long long`。

**线段相交漏掉端点接触。** 严格跨立判断只覆盖一般相交；端点和共线重叠需要 `on_segment`。

**凸包共线策略不明确。** `cross <= 0` 会移除共线中间点；如果题目要求保留边界所有点，需要改成只在 `cross < 0` 时弹出并处理重复点。

**只画图判断。** 几何样例应写出叉积符号和包围盒条件，否则很难覆盖端点接触和共线重叠。

## 练习

1. 改成保留凸包边界上的所有共线点。
2. 实现点在凸多边形内的 `O(log n)` 判断。
3. 用扫描线检测多条线段是否存在交点。
4. 改用 `long double` 处理圆和直线交点，并讨论误差阈值。

## 参考资料

- [cp-algorithms: Basic Geometry](https://cp-algorithms.com/geometry/basic-geometry.html)
- [cp-algorithms: Convex Hull construction](https://cp-algorithms.com/geometry/convex-hull.html)
- [cppreference: std::sort](https://en.cppreference.com/w/cpp/algorithm/sort)
{% endraw %}
