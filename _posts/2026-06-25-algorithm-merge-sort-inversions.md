---
layout: post
title: "归并排序与逆序对：在合并时计算跨区间关系"
date: 2026-06-25 05:15:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用归并排序解释分治、稳定合并和逆序对计数，展示为什么跨左右半区的关系可以在 merge 阶段一次性统计。"
tags: [algorithm, merge-sort, divide-and-conquer, inversion-count, cplusplus]
---
{% raw %}

> 主题：排序 / 分治 / 逆序对 / C++ 可复现实验  
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含随机数组与朴素逆序对计数对照。

排序不只是把数组变有序。归并排序展示了分治算法的基本结构：把问题拆成左右两半，递归解决，再把两个已解决的结果合并。逆序对计数则说明，分治还可以在合并阶段统计跨子问题的关系。

如果直接枚举所有 `(i, j)`，逆序对需要 `O(n^2)`。归并排序把左右半区分别排好后，跨区间逆序对可以用两个指针线性统计，整体降到 `O(n log n)`。

## 学习目标

1. 解释分治的“拆分、解决、合并”结构。
2. 写出稳定归并排序的核心合并逻辑。
3. 理解逆序对为什么可以在 merge 阶段计数。
4. 区分排序正确性和额外统计量正确性。
5. 用朴素 `O(n^2)` 模型验证逆序对数量。

## 核心模型

![归并排序与逆序对](/assets/diagrams/algorithm-merge-sort-inversions.svg)

左右半区已经有序时，如果 `left[i] <= right[j]`，左边当前元素不会和 `right[j]` 构成逆序，直接输出。否则 `right[j]` 小于 `left[i]`，并且也小于 `left[i..mid)` 中所有剩余元素，于是一次增加 `mid - i` 个逆序对。

## C++ 实现

核心递归函数：

```cpp
long long merge_count(std::vector<int>& a,
                      std::vector<int>& tmp,
                      int l, int r) {
    if (r - l <= 1) return 0;
    int m = l + (r - l) / 2;
    long long inv = merge_count(a, tmp, l, m)
                  + merge_count(a, tmp, m, r);
    int i = l, j = m, k = l;
    while (i < m || j < r) {
        if (j == r || (i < m && a[i] <= a[j])) {
            tmp[k++] = a[i++];
        } else {
            tmp[k++] = a[j++];
            inv += m - i;
        }
    }
    for (int t = l; t < r; ++t) a[t] = tmp[t];
    return inv;
}
```

`a[i] <= a[j]` 时先拿左边元素，这让相等元素保持原相对顺序，也是稳定合并的关键。逆序对定义通常是 `a[i] > a[j]`，相等值不计入逆序。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
input: 5 2 4 2 1
sorted: 1 2 2 4 5
inversions=8
merge step counts how many left-half elements a right-half element jumps over
```

随机测试生成 500 组数组，检查两件事：排序结果必须等于 `std::sort`；逆序对数量必须等于朴素双重循环。两个断言缺一不可，因为排序正确不代表统计量正确。

## 正确性思路

递归假设左右半区已经排好，并且各自内部逆序对已经正确计算。合并阶段只剩跨左右半区的逆序对。由于左右有序，当 `a[i] > a[j]` 时，左半区从 `i` 到 `m - 1` 的所有元素都大于 `a[j]`，一次加 `m - i` 不会多算或漏算。每个跨区间逆序对都在它首次分属左右两半的那一层被统计一次。

## 复杂度

递归层数是 `log n`，每层总合并代价是 `O(n)`，所以时间复杂度 `O(n log n)`。辅助数组 `tmp` 大小为 `O(n)`。逆序对数量最大约为 `n(n-1)/2`，计数变量应使用 `long long`。

## 常见错误

**相等元素被误计为逆序。** 如果条件写成 `a[i] < a[j]` 才取左边，那么相等值会走右边分支，容易把相等元素算进逆序。

**每次递归都重新分配临时数组。** 这会增加不必要开销。实验代码在外层分配一次 `tmp`，递归复用。

**只测排序，不测计数。** 逆序对统计是附加逻辑，必须用独立 oracle 验证。

## 练习

1. 输出每一层 merge 的 `[l, r)` 范围和本层新增逆序数。
2. 修改代码，让它返回排序后的新数组，保留原数组不被改写。
3. 用逆序对判断一个排列距离有序状态的程度。
4. 思考快速排序为什么不适合直接统计逆序对。

## 参考资料

- [MIT OpenCourseWare 6.006 Syllabus](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/pages/syllabus/)
- [Princeton Algorithms, Part I](https://algs4.cs.princeton.edu/home/)
- [cppreference: std::stable_sort](https://en.cppreference.com/w/cpp/algorithm/stable_sort)
{% endraw %}
