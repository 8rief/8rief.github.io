---
layout: post
title: "双指针与滑动窗口：让每个元素最多进出一次"
date: 2026-06-25 05:10:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用最短正数子数组和最长无重复子数组解释双指针的单调移动条件、窗口不变量和 O(n) 摊还复杂度。"
tags: [algorithm, two-pointers, sliding-window, cplusplus, invariants]
---
{% raw %}

> 主题：双指针 / 滑动窗口 / 摊还复杂度 / C++ 可复现实验  
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含固定样例和随机朴素对照。

双指针经常被误解成“两个下标一起移动”。真正重要的是单调性：每个指针只朝一个方向移动，因此每个元素进入窗口一次、离开窗口一次。只要窗口性质能通过移动左端点恢复，就可能把本来 `O(n^2)` 的枚举压到 `O(n)`。

本文用两个代表问题建立模型：正数数组中和至少为 `target` 的最短子数组，以及最长无重复元素子数组。前者依赖正数保证窗口和随右端扩张单调增加；后者依赖哈希表记录上次出现位置，让左端点跳到合法边界。

## 学习目标

1. 解释双指针成立所需的单调移动条件。
2. 写出滑动窗口里的窗口含义和恢复规则。
3. 区分正数数组的窗口和包含负数时的限制。
4. 用朴素 `O(n^2)` 模型验证窗口算法。
5. 用摊还分析说明 `O(n)` 的来源。

## 核心模型

![双指针与滑动窗口](/assets/diagrams/algorithm-two-pointers-sliding-window.svg)

窗口通常写成 `[left, right]` 或 `[left, right)`。右端点负责把新元素纳入候选范围，左端点负责在条件被破坏或可以收缩时恢复最小合法窗口。只要 `left` 不回退，总移动次数就被 `2n` 级别控制。

## 问题一：和至少为 target 的最短正数子数组

```cpp
int min_subarray_len_at_least(const std::vector<int>& a, int target) {
    int best = INT_MAX;
    int sum = 0;
    std::size_t left = 0;
    for (std::size_t right = 0; right < a.size(); ++right) {
        sum += a[right];
        while (sum >= target) {
            best = std::min(best, static_cast<int>(right - left + 1));
            sum -= a[left++];
        }
    }
    return best == INT_MAX ? 0 : best;
}
```

这个写法依赖数组元素为正。右端扩张会让 `sum` 增大，左端收缩会让 `sum` 减小；因此一旦 `sum >= target`，可以放心尝试收缩左端，直到窗口不再合法。

## 问题二：最长无重复子数组

```cpp
int longest_distinct_subarray(const std::vector<int>& a) {
    std::unordered_map<int, std::size_t> last;
    std::size_t left = 0;
    int best = 0;
    for (std::size_t right = 0; right < a.size(); ++right) {
        auto it = last.find(a[right]);
        if (it != last.end() && it->second >= left) {
            left = it->second + 1;
        }
        last[a[right]] = right;
        best = std::max(best, static_cast<int>(right - left + 1));
    }
    return best;
}
```

窗口不变量是：`[left, right]` 内没有重复元素。遇到重复值时，左端点直接跳过上一次出现位置。这里不能写成 `left = last[x] + 1` 而不检查 `last[x] >= left`，否则会让左端点倒退。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
min length with sum>=7: 2
longest distinct window: 3
invariant: left pointer only moves right, so every element enters and leaves the window at most once
```

测试策略：最短子数组在随机正数数组上对照 `O(n^2)` 枚举；最长无重复子数组在小值域随机数组上对照朴素窗口枚举。这样能验证找不到答案、重复值密集、窗口反复收缩等边界。

## 正确性思路

最短正数子数组的关键是“当前右端点固定时，持续右移左端点会枚举所有以 `right` 结尾的最短合法候选”。由于元素为正，收缩会让和下降，不会漏掉更短候选。

最长无重复子数组的关键是“左端点始终是使当前窗口无重复的最小安全边界”。当 `a[right]` 在窗口内出现过，任何不越过旧位置的窗口都非法；跳到旧位置后一格正好恢复不变量。

## 复杂度

两个算法都是 `O(n)` 级别。虽然代码里有 `while`，但每个元素最多被右端加入一次、被左端移出一次。最长无重复子数组额外使用哈希表，平均 `O(n)` 时间、`O(k)` 空间，其中 `k` 是窗口内可能出现的不同值数量。

## 常见错误

**在包含负数的数组上直接套正数窗口。** 如果有负数，右端扩张不一定增大和，左端收缩不一定减小和，单调性消失。

**左指针倒退。** 处理上次出现位置时，要确认它仍在当前窗口内。

**只记住模板，不写窗口含义。** 每道题都应先写清楚窗口内维护什么性质，再决定移动规则。

## 练习

1. 实现“最长至多包含两个不同值的子数组”。
2. 把最短子数组问题改成允许负数，尝试用前缀和和单调队列解决。
3. 输出每一步 `left/right/sum`，观察窗口如何收缩。
4. 证明每个指针最多移动 `n` 次。

## 参考资料

- [Princeton Algorithms, Part I](https://algs4.cs.princeton.edu/home/)
- [cppreference: std::unordered_map](https://en.cppreference.com/w/cpp/container/unordered_map)
- [MIT OpenCourseWare 6.006 Syllabus](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/pages/syllabus/)
{% endraw %}
