---
layout: post
title: "随机化 Quickselect：只找第 k 小，不排序整组"
date: 2026-06-25 15:41:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从选择问题出发，解释随机 pivot、三路划分、只递归答案所在一侧和期望线性复杂度。"
tags: [algorithm, quickselect, randomized-algorithm, order-statistic, cplusplus]
---
{% raw %}
> 主题：Quickselect / Order Statistic / Randomized Algorithm / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

如果只需要第 `k` 小元素，完整排序会产生多余顺序信息。Quickselect 使用快速排序的划分思想：随机选择 pivot，把数组划成小于、等于、大于三段，然后只保留包含第 `k` 小的那一段继续处理。

## 学习目标

1. 把选择问题和排序问题分开建模。
2. 实现三路划分，处理大量重复元素。
3. 说明随机化如何降低固定坏例风险。
4. 用排序结果作为 oracle 验证第 `k` 小。
5. 区分期望复杂度和最坏复杂度。

## 核心模型

![随机化 Quickselect 流程](/assets/diagrams/algorithm-randomized-quickselect.svg)

三路划分后，如果 `k` 落在等于 pivot 的区间内，pivot 就是答案；如果落在左段或右段，另一侧的所有元素都可以丢弃。

## C++ 实现片段

```cpp
int quickselect(std::vector<int> a, int k, std::mt19937& rng) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (true) {
        int pivot = a[std::uniform_int_distribution<int>(lo, hi - 1)(rng)];
        int lt = lo, i = lo, gt = hi;
        while (i < gt) {
            if (a[i] < pivot) std::swap(a[lt++], a[i++]);
            else if (a[i] > pivot) std::swap(a[i], a[--gt]);
            else ++i;
        }
        if (k < lt) hi = lt;
        else if (k >= gt) lo = gt;
        else return pivot;
    }
}
```

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
array: 9 1 5 7 3 3 8
k=3 zero-based -> kth value=5
sorted check: 1 3 3 5 7 8 9
```

随机测试生成 500 个数组，选择随机 `k`，把 Quickselect 结果和排序后的第 `k` 个元素比较。重复元素样例检查等值段能否一次处理完。

## 正确性思路

划分后，左段元素都小于 pivot，中段都等于 pivot，右段都大于 pivot。第 `k` 小元素只可能落在一个区域内。算法每轮根据 `k` 与三段边界缩小候选区间，并保留答案所在区域。

随机 pivot 的期望分析来自规模缩减：pivot 进入中间排名区间时，下一轮规模会显著下降；坏 pivot 可能出现，但长期期望总处理量为线性。

## 常见错误

- 两路划分在重复元素很多时退化明显。
- 混淆 0-based 与 1-based 的 `k`。
- 把随机化期望界当成确定性最坏界。

## 练习

1. 改成原地版本，并说明函数会重排输入。
2. 实现 median-of-medians，获得确定性最坏线性。
3. 用 Quickselect 找中位数并计算绝对偏差和。
4. 统计不同随机种子下的划分轮数。

## 参考资料

- [cp-algorithms: K-th order statistic in O(N)](https://cp-algorithms.com/sequences/k-th.html)
- [Princeton Algorithms: Quicksort](https://algs4.cs.princeton.edu/23quicksort/)
- [cppreference: std::mt19937](https://en.cppreference.com/w/cpp/numeric/random/mersenne_twister_engine)
{% endraw %}
