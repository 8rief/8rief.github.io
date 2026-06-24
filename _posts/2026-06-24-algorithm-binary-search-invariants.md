---
layout: post
title: "二分查找不只是 mid：用不变量写对边界"
date: 2026-06-24 16:20:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从 lower_bound 的半开区间不变量出发，讲清二分查找边界、正确性和 C++ 测试验证。"
tags: [algorithm, binary-search, cpp, invariant, testing]
---
{% raw %}

> 主题：算法与数据结构 / 二分查找 / 循环不变量 / C++ 实现  
> 本文命令已在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下本地执行验证。实验覆盖 Debug 构建、CTest、固定边界测试、trace 不变量检查，以及 300 轮随机数组与 `std::lower_bound` / `std::upper_bound` 对照。

二分查找的代码很短，但它是最容易“看起来会写、实际边界错一格”的算法之一。错误通常不在 `mid = (left + right) / 2` 这一行，而在没有说明循环到底维护什么事实：`left` 左边是什么？`right` 右边是什么？答案允许等于 `right` 吗？空数组如何表示？全都小于目标值时返回哪里？

这篇文章用 `lower_bound` 作为主线：在一个有序数组中找第一个 `values[i] >= target` 的位置。这个定义比“找某个数”更稳定，因为它自然覆盖了不存在、重复、插入位置和空数组。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 用半开区间 `[left, right)` 描述二分查找的搜索范围。
2. 解释 `lower_bound` 的不变量：左侧都小于目标，右侧都大于等于目标。
3. 写出 `lower_bound`、`upper_bound` 和 `contains` 的 C++20 实现。
4. 用固定边界、trace 检查和随机对照验证实现。
5. 说明时间复杂度为什么是 `O(log n)`，以及它依赖数组已经有序这一前提。

## 问题模型

输入：一个按非降序排列的整数数组 `values` 和一个目标值 `target`。

输出：第一个满足 `values[i] >= target` 的下标。如果不存在这样的下标，返回 `values.size()`。

这个输出定义有三个好处：

- 空数组返回 `0`，不需要特殊哨兵；
- 目标值不存在时，返回它应该插入的位置；
- 重复元素存在时，返回重复块的第一个位置。

`upper_bound` 只把条件换成第一个 `values[i] > target`。有了这两个位置，重复元素区间就是 `[lower_bound, upper_bound)`。

## 核心不变量

二分查找每轮维护三段区域：

![二分查找半开区间不变量](/assets/diagrams/algorithm-binary-search-invariants.svg)

对 `lower_bound` 来说，不变量是：

1. `[0, left)` 中所有元素都满足 `values[i] < target`，所以答案不在左侧。
2. `[right, n)` 中所有元素都满足 `values[i] >= target`，所以如果答案已经被排到右侧，最靠左可能就是 `right`。
3. `[left, right)` 是未知区间，答案只可能在这里。

初始化时 `left = 0`、`right = n`，左右两侧都是空区间，不变量成立。循环每次取 `mid`：

- 如果 `values[mid] >= target`，`mid` 可能是答案，`mid` 右侧也都不会比它更靠左，因此令 `right = mid`。
- 如果 `values[mid] < target`，`mid` 和它左侧都不可能是答案，因此令 `left = mid + 1`。

循环在 `left == right` 时停止。未知区间为空，答案就是这个分界点。

## C++ 实现

项目结构：

```text
algorithms-binary-search-invariants/
├── CMakeLists.txt
├── include/search/binary_search.hpp
├── src/binary_search.cpp
├── src/main.cpp
└── tests/test_binary_search.cpp
```

核心接口：

```cpp
#pragma once
#include <cstddef>
#include <functional>
#include <span>
#include <vector>

namespace search {

struct Step {
    std::size_t left;
    std::size_t mid;
    std::size_t right;
    int mid_value;
};

std::size_t first_true(std::size_t left, std::size_t right, const std::function<bool(std::size_t)>& pred);
std::size_t lower_bound_index(std::span<const int> values, int target);
std::size_t upper_bound_index(std::span<const int> values, int target);
bool contains(std::span<const int> values, int target);
std::vector<Step> lower_bound_trace(std::span<const int> values, int target);

}  // namespace search
```

实现时先写通用的 `first_true`：在 `[left, right)` 上找第一个让谓词为真的位置。

```cpp
std::size_t first_true(std::size_t left, std::size_t right, const std::function<bool(std::size_t)>& pred) {
    while (left < right) {
        const std::size_t mid = left + (right - left) / 2;
        if (pred(mid)) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}

std::size_t lower_bound_index(std::span<const int> values, int target) {
    return first_true(0, values.size(), [&](std::size_t i) { return values[i] >= target; });
}

std::size_t upper_bound_index(std::span<const int> values, int target) {
    return first_true(0, values.size(), [&](std::size_t i) { return values[i] > target; });
}

bool contains(std::span<const int> values, int target) {
    const std::size_t pos = lower_bound_index(values, target);
    return pos < values.size() && values[pos] == target;
}
```

`mid` 的写法使用 `left + (right - left) / 2`，避免 `left + right` 在大整数下溢出或溢出的风险。`std::span<const int>` 让函数接收连续数组视图，不接管所有权，也不复制数据。

为了教学和调试，额外提供 trace：

```cpp
std::vector<Step> lower_bound_trace(std::span<const int> values, int target) {
    std::vector<Step> steps;
    std::size_t left = 0;
    std::size_t right = values.size();
    while (left < right) {
        const std::size_t mid = left + (right - left) / 2;
        steps.push_back(Step{left, mid, right, values[mid]});
        if (values[mid] >= target) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return steps;
}
```

## 验证策略

固定边界测试覆盖最容易错的情况：空数组、目标在最左侧之前、重复块、目标在最右侧之后、存在与不存在。

```cpp
void test_fixed_boundaries() {
    const std::vector<int> empty;
    require(search::lower_bound_index(empty, 10) == 0, "empty lower_bound");
    const std::vector<int> values{1, 2, 4, 4, 4, 7};
    require(search::lower_bound_index(values, 0) == 0, "before first");
    require(search::lower_bound_index(values, 4) == 2, "first duplicate");
    require(search::upper_bound_index(values, 4) == 5, "after duplicate block");
    require(search::lower_bound_index(values, 8) == values.size(), "after last");
    require(search::contains(values, 7), "contains existing");
    require(!search::contains(values, 3), "does not contain gap");
}
```

trace 测试直接检查不变量：每一步 `mid` 都在半开区间内；`left` 左侧都小于目标；`right` 右侧都大于等于目标。

```cpp
void test_trace_invariant() {
    const std::vector<int> values{1, 2, 4, 4, 4, 7, 9};
    const int target = 4;
    for (const auto& step : search::lower_bound_trace(values, target)) {
        require(step.left <= step.mid && step.mid < step.right, "mid inside half-open interval");
        for (std::size_t i = 0; i < step.left; ++i) {
            require(values[i] < target, "left side already false");
        }
        for (std::size_t i = step.right; i < values.size(); ++i) {
            require(values[i] >= target, "right side already true");
        }
    }
}
```

随机对照测试用标准库作为参考实现。它不会证明算法，但能快速捕捉大量边界偏差。

```cpp
void test_against_standard_library() {
    std::mt19937 rng(20260624);
    std::uniform_int_distribution<int> size_dist(0, 40);
    std::uniform_int_distribution<int> value_dist(-20, 20);
    for (int round = 0; round < 300; ++round) {
        std::vector<int> values(size_dist(rng));
        for (int& value : values) {
            value = value_dist(rng);
        }
        std::sort(values.begin(), values.end());
        for (int target = -25; target <= 25; ++target) {
            const auto expected_lower = static_cast<std::size_t>(std::lower_bound(values.begin(), values.end(), target) - values.begin());
            const auto expected_upper = static_cast<std::size_t>(std::upper_bound(values.begin(), values.end(), target) - values.begin());
            require(search::lower_bound_index(values, target) == expected_lower, "lower_bound matches std");
            require(search::upper_bound_index(values, target) == expected_upper, "upper_bound matches std");
        }
    }
}
```

## 执行实验

构建并运行测试：

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
```

本地输出：

```text
100% tests passed, 0 tests failed out of 1
```

运行示例程序：

```bash
./build/binary_search_demo
```

输出：

```text
values: 1 2 4 4 4 7 9 
target=4 lower_bound=2 upper_bound=5
[0, 7) mid=3 value=4
[0, 3) mid=1 value=2
[2, 3) mid=2 value=4
```

这段 trace 对应不变量的收缩过程。第一次 `mid=3` 值为 4，说明答案在 `[0,3]` 内，改成半开区间就是 `[0,3)`；第二次 `mid=1` 值为 2，说明 `[0,1]` 都不是答案，区间收缩为 `[2,3)`；第三次 `mid=2` 值为 4，最终停在位置 2。

## 正确性理由

正确性由循环不变量推出：

- 初始化：`[0,left)` 和 `[right,n)` 都为空，不变量成立。
- 保持：每轮根据 `values[mid] >= target` 是否成立，把 `mid` 归入右侧候选或归入左侧排除区，不变量仍成立。
- 终止：`left == right` 时未知区间为空。左边所有位置都小于目标，右边所有位置都大于等于目标，所以分界点就是第一个大于等于目标的位置。

算法每轮至少把未知区间长度减半，所以循环次数是 `O(log n)`。空间复杂度是 `O(1)`；如果保存 trace，则额外空间是 `O(log n)`。这个复杂度成立的前提是数组已经有序。如果输入无序，不变量从第一轮就不成立，二分结果没有意义。

## 常见错误

**混用闭区间和半开区间。** 如果代码写 `[left, right]`，更新规则和终止条件都要跟着改变。本文选择 `[left, right)`，是因为它天然支持空区间，也和 C++ 标准库迭代器范围一致。

**找到等于目标就立即返回。** 这只能判断“存在某个目标”，不能保证返回重复块的第一个位置。`lower_bound` 的目标是边界，不是任意匹配。

**忘记全都小于目标的情况。** 当目标大于所有元素时，正确返回值是 `values.size()`。调用方必须先检查下标是否小于数组长度，再读取元素。

**用随机测试替代不变量。** 随机对照能发现很多错误，但它不能解释为什么算法正确。算法题最重要的部分仍然是问题模型和不变量。

## 练习

1. 把 `lower_bound_index()` 改成闭区间版本，写出新的不变量和终止条件。
2. 实现 `equal_range_index()`，返回重复块 `[lower_bound, upper_bound)`。
3. 删除 `mid = left + (right - left) / 2` 中的安全写法，思考在大下标时有什么风险。
4. 把随机测试中的数组排序步骤删掉，观察和标准库对照测试会出现什么问题。

## 参考资料

- [cppreference: `std::lower_bound`](https://en.cppreference.com/w/cpp/algorithm/lower_bound)
- [cppreference: `std::upper_bound`](https://en.cppreference.com/w/cpp/algorithm/upper_bound)
- [cp-algorithms: Binary Search](https://cp-algorithms.com/num_methods/binary_search.html)
- Thomas H. Cormen et al., *Introduction to Algorithms*, 4th edition, chapter on divide-and-conquer and searching.
{% endraw %}
