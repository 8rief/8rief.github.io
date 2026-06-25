---
layout: post
title: "计算几何基础：方向、线段相交和凸包"
date: 2026-06-25 14:30:00 +0800
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

## 学习目标

1. 用整数叉积实现 orientation，避免小规模整数输入中的浮点误差。
2. 写出包含端点和共线情况的线段相交判断。
3. 实现 Andrew monotonic chain 凸包。
4. 解释凸包中共线点保留策略。
5. 用固定样例验证边界行为。

## 核心模型

![计算几何基础链条](/assets/diagrams/algorithm-computational-geometry-basics.svg)

方向判断是底层谓词。线段相交使用两组方向和包围盒检查；凸包则按排序后的点序维护只向同一方向转的边界链。

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

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
convex hull: (0,0) (2,0) (2,2) (0,2)
segments intersect=true
```

凸包样例包含正方形内部点和边界点，输出四个角。线段相交样例覆盖真正交叉；测试里还包含共线重叠和共线分离，保证端点与包围盒逻辑正确。

## 正确性思路

两条线段严格相交时，线段 `cd` 的两个端点位于有向直线 `ab` 两侧，线段 `ab` 的两个端点也位于有向直线 `cd` 两侧。共线或端点接触时，两侧判断会退化到 0，因此需要额外检查点是否落在线段包围盒内。

凸包维护时，排序后的点从左到右加入。下凸壳中如果最后两个点与新点形成非左转，末尾点无法成为严格凸边界点，可以弹出。上凸壳同理。两条链合并后得到逆时针凸包。

## 复杂度

- 方向判断和线段相交：`O(1)`。
- Andrew 凸包：排序 `O(n log n)`，维护栈总计 `O(n)`。
- 空间：凸包和排序数组 `O(n)`。

## 常见错误

**用 int 存叉积。** 坐标达到 `1e9` 时，乘积会超过 32 位范围。本文使用 `long long`。

**线段相交漏掉端点接触。** 严格跨立判断只覆盖一般相交；端点和共线重叠需要 `on_segment`。

**凸包共线策略不明确。** `cross <= 0` 会移除共线中间点；如果题目要求保留边界所有点，需要改成只在 `cross < 0` 时弹出并处理重复点。

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
