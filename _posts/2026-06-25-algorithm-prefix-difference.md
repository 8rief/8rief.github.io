---
layout: post
title: "前缀和与差分数组：把区间问题变成边界问题"
date: 2026-06-25 05:05:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用半开区间、前缀和和差分数组统一理解区间求和与批量区间加法，并用随机测试对照朴素模型。"
tags: [algorithm, prefix-sum, difference-array, cplusplus, invariants]
---
{% raw %}

> 主题：数组区间模型 / 前缀和 / 差分数组 / C++ 可复现实验  
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。代码只使用本地固定输入和随机对照测试。

数组区间题常见两类操作：查询一段区间的和，或者给一段区间统一加一个值。直接枚举区间当然能做，但当查询或更新次数很多时，真正的瓶颈在于区间边界有没有被抽象出来。

前缀和与差分数组正好互为镜像：前缀和把多个元素的求和变成两个边界值相减；差分数组把整段更新变成两个边界点的增减。学会这两个模型，后面的二维前缀和、扫描线、Fenwick 树和线段树都会更自然。

## 学习目标

读完并执行实验后，你应该能够：

1. 用半开区间 `[l, r)` 表达区间边界。
2. 解释为什么 `sum(l, r) = prefix[r] - prefix[l]`。
3. 用差分数组完成多次区间加法。
4. 说明前缀和适合静态多查询，差分适合离线批量更新。
5. 用朴素模型随机测试边界正确性。

## 核心模型

![前缀和与差分数组](/assets/diagrams/algorithm-prefix-difference.svg)

对数组 `a` 定义：

```text
prefix[0] = 0
prefix[i + 1] = prefix[i] + a[i]
```

于是半开区间 `[l, r)` 的和等于：

```text
a[l] + a[l+1] + ... + a[r-1] = prefix[r] - prefix[l]
```

差分数组反过来描述“变化量”。对 `[l, r)` 加 `delta` 时，只需要：

```text
diff[l] += delta
diff[r] -= delta
```

最后从左到右累加 `diff`，就能恢复每个位置的最终值。

## C++ 实现

前缀和函数：

```cpp
std::vector<long long> build_prefix(const std::vector<long long>& a) {
    std::vector<long long> prefix(a.size() + 1, 0);
    for (std::size_t i = 0; i < a.size(); ++i) {
        prefix[i + 1] = prefix[i] + a[i];
    }
    return prefix;
}

long long range_sum(const std::vector<long long>& prefix,
                    std::size_t l, std::size_t r) {
    return prefix[r] - prefix[l];
}
```

差分批量更新：

```cpp
std::vector<long long> apply_range_adds(
    std::size_t n,
    const std::vector<std::tuple<std::size_t, std::size_t, long long>>& ops) {
    std::vector<long long> diff(n + 1, 0);
    for (auto [l, r, delta] : ops) {
        diff[l] += delta;
        diff[r] -= delta;
    }
    std::vector<long long> a(n, 0);
    long long cur = 0;
    for (std::size_t i = 0; i < n; ++i) {
        cur += diff[i];
        a[i] = cur;
    }
    return a;
}
```

这里统一使用半开区间 `[l, r)`。好处是空区间自然表示为 `l == r`，长度是 `r - l`，前缀数组的下标也刚好对齐。

## 实验输出

实验脚本执行了 CMake/Ninja 构建、CTest 和 demo：

```text
100% tests passed, 0 tests failed out of 1
array: 2 4 -3 7 1
prefix: 0 2 6 3 10 11
sum[1,4)=8
range-add result: 5 5 3 -2 -2
```

测试包含两部分：固定样例检查具体值；400 轮随机数组和随机区间，把前缀和查询与朴素求和对照，把差分更新结果与逐元素更新对照。随机对照的价值在于覆盖空区间、负数、全区间和短数组等手写样例容易漏掉的边界。

## 正确性思路

前缀和的正确性来自抵消：`prefix[r]` 包含 `[0, r)` 的所有元素，`prefix[l]` 包含 `[0, l)` 的所有元素，相减后只剩 `[l, r)`。

差分数组的正确性来自边界事件：在 `l` 处开始增加 `delta`，在 `r` 处撤销这次增加。扫描到区间内部时，累积变化量包含这次更新；扫描到 `r` 以后，这次更新被抵消。

## 复杂度

- 建前缀和：`O(n)` 时间、`O(n)` 空间。
- 单次区间求和：`O(1)`。
- `m` 次差分区间更新后恢复数组：`O(n + m)`。
- 如果需要边更新边查询，差分数组就不够了，应转向 Fenwick 树或线段树。

## 常见错误

**混用闭区间和半开区间。** 如果文章、代码和测试同时出现 `[l, r]` 与 `[l, r)`，边界错误会迅速增加。建议初学阶段统一半开区间。

**忘记差分数组需要 `n + 1` 个位置。** 更新 `[l, r)` 要写 `diff[r] -= delta`，当 `r == n` 时仍需要合法位置。

**把前缀和用于频繁在线更新。** 前缀和适合静态数组。数组频繁改变时，每次重建前缀和代价太高。

## 练习

1. 把 `range_sum` 改成闭区间 `[l, r]` 版本，并写出对应测试。
2. 在二维矩阵上实现二维前缀和。
3. 用差分数组解决“航班预订统计”类批量区间加法问题。
4. 思考：如果要支持“单点修改 + 区间求和”，为什么 Fenwick 树更合适？

## 参考资料

- [MIT OpenCourseWare 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)
- [cppreference: std::partial_sum](https://en.cppreference.com/w/cpp/algorithm/partial_sum)
- [cp-algorithms: Fenwick Tree](https://cp-algorithms.com/data_structures/fenwick.html)
{% endraw %}
