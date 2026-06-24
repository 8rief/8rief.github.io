---
layout: post
title: "单调栈：用栈保存还没有找到边界的元素"
date: 2026-06-25 05:20:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从 next greater 到柱状图最大矩形，解释单调栈如何维护候选边界，并用朴素模型验证 O(n) 算法。"
tags: [algorithm, monotonic-stack, stack, cplusplus, amortized-analysis]
---
{% raw %}

> 主题：单调栈 / 最近更大更小元素 / 柱状图最大矩形 / C++ 可复现实验  
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含 next greater、previous less 和 largest rectangle 的随机朴素对照。

单调栈解决的是一类边界问题：对每个位置，找到左边或右边第一个比它大或小的元素。暴力做法从每个位置向外扫描，最坏 `O(n^2)`；单调栈把还没有找到答案的元素放进栈里，当新元素出现时一次性结算被它击败的候选。

这个思想非常常用：每日温度、下一个更大元素、接雨水、柱状图最大矩形、可见山峰、贡献法统计子数组最小值，都可以从同一个模型出发。

## 学习目标

1. 解释单调栈里保存的是什么候选。
2. 写出 next greater 和 previous less 两种方向的代码。
3. 用弹栈时刻理解“右边第一个边界”。
4. 理解柱状图最大矩形中的左右边界。
5. 用摊还分析说明为什么总复杂度是 `O(n)`。

## 核心模型

![单调栈边界模型](/assets/diagrams/algorithm-monotonic-stack.svg)

以 next greater 为例，栈中下标对应的值保持单调不增。新值 `a[i]` 到来时，只要它大于栈顶，就说明栈顶元素的“右侧第一个更大值”已经找到，答案就是 `i`。弹出的元素不会再回栈。

## next greater

```cpp
std::vector<int> next_greater_index(const std::vector<int>& a) {
    std::vector<int> ans(a.size(), -1), st;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        while (!st.empty() && a[st.back()] < a[i]) {
            ans[st.back()] = i;
            st.pop_back();
        }
        st.push_back(i);
    }
    return ans;
}
```

栈里放下标更稳妥，因为答案通常需要位置，后续也可能要计算距离或宽度。

## previous less

```cpp
std::vector<int> previous_less_index(const std::vector<int>& a) {
    std::vector<int> ans(a.size(), -1), st;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        while (!st.empty() && a[st.back()] >= a[i]) st.pop_back();
        ans[i] = st.empty() ? -1 : st.back();
        st.push_back(i);
    }
    return ans;
}
```

这里使用 `>=` 弹栈，是为了让栈顶严格小于当前值。等号如何处理要根据题意决定：你要的是“严格更小”还是“小于等于”。

## 柱状图最大矩形

当某个柱子被更矮的柱子弹出时，说明它的右边界已经确定；弹栈后新的栈顶就是左边第一个更矮柱子。于是以这个高度为最低高度的最大宽度可以立刻计算。

```cpp
int largest_rectangle_area(const std::vector<int>& h) {
    std::vector<int> st;
    int best = 0;
    for (int i = 0; i <= static_cast<int>(h.size()); ++i) {
        int cur = (i == static_cast<int>(h.size())) ? 0 : h[i];
        while (!st.empty() && h[st.back()] > cur) {
            int height = h[st.back()];
            st.pop_back();
            int left = st.empty() ? -1 : st.back();
            best = std::max(best, height * (i - left - 1));
        }
        st.push_back(i);
    }
    return best;
}
```

末尾补一个高度为 0 的哨兵，可以把栈里剩余柱子统一弹出。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
array: 2 1 2 4 3
next greater index: 3 2 3 -1 -1
largest rectangle of 2 1 5 6 2 3 = 10
```

测试用朴素扫描验证 next greater 和 previous less，用 `O(n^2)` 枚举所有区间验证柱状图最大矩形。500 轮随机测试覆盖重复值、全递增、全递减和空数组等情况。

## 正确性思路

对 next greater，元素在栈中等待第一个能弹出它的右侧元素。由于从左到右扫描，第一次弹出它的元素一定是右侧最近的位置；由于弹出条件是更大值，这个位置满足题意。

对柱状图，某个高度 `h[k]` 被弹出时，当前 `i` 是右侧第一个比它矮的位置，弹栈后的栈顶是左侧第一个比它矮的位置。两个边界之间的所有柱子高度都至少为 `h[k]`，因此宽度最大。

## 复杂度

每个下标入栈一次、出栈一次，所有 while 循环总弹栈次数不超过 `n`，所以时间复杂度是 `O(n)`，空间复杂度 `O(n)`。

## 常见错误

**等号处理不清。** `>`、`>=`、`<`、`<=` 对重复值影响很大。先写清楚要找“严格”边界还是“非严格”边界。

**栈里存值导致距离丢失。** 多数边界题需要下标。

**忘记清空栈。** 柱状图这类题需要末尾哨兵或循环后补处理。

## 练习

1. 实现“每日温度”问题，返回等待天数。
2. 实现每个元素左侧第一个更大值。
3. 修改柱状图代码，输出最大矩形的左右边界。
4. 思考单调队列和单调栈的区别。

## 参考资料

- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
- [Princeton Algorithms, Part I](https://algs4.cs.princeton.edu/home/)
- [MIT OpenCourseWare 6.006 Syllabus](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/pages/syllabus/)
{% endraw %}
