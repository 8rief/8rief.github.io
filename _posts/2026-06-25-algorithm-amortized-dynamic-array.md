---
layout: post
title: "摊还分析：动态数组扩容为什么均摊 O(1)"
date: 2026-06-25 15:40:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用动态数组倍增扩容实验解释聚合分析：单次扩容可能很贵，但连续 push 的总复制次数受几何级数限制。"
tags: [algorithm, amortized-analysis, dynamic-array, cplusplus]
---
{% raw %}
> 主题：Amortized Analysis / Dynamic Array / 聚合分析 / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

动态数组的 `push_back` 有时只写入一个元素，有时会触发扩容并复制全部旧元素。单次最坏复杂度可能达到 `O(n)`，但连续执行很多次插入时，倍增扩容的总成本仍是线性的。摊还分析研究的正是这种“局部峰值高、整体平均低”的操作序列。

## 学习目标

1. 区分单次最坏复杂度和均摊复杂度。
2. 用聚合分析证明倍增扩容的复制总量小于线性上界。
3. 写出可记录复制次数、写入次数和容量轨迹的模型。
4. 说明按 1 增长容量为什么会退化。
5. 用实验输出解释均摊 `O(1)` 的含义。

## 核心模型

![动态数组摊还分析](/assets/diagrams/algorithm-amortized-dynamic-array.svg)

倍增扩容的容量轨迹是 `1,2,4,8,...`。复制旧元素的总数是一个几何级数；插入 `n` 个元素时，扩容复制总量小于 `2n`，再加上 `n` 次新元素写入，总工作量仍是 `O(n)`。

## C++ 实现片段

```cpp
void push_back(int value) {
    if (size_ == static_cast<int>(storage_.size())) {
        grow();
    }
    storage_[size_++] = value;
    ++writes_;
}

void grow() {
    int new_capacity = storage_.empty() ? 1 : storage_.size() * 2;
    std::vector<int> next(new_capacity);
    for (int i = 0; i < size_; ++i) {
        next[i] = storage_[i];
        ++copied_;
    }
    storage_ = std::move(next);
}
```

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
after 20 pushes: size=20 capacity=32 copied=31 writes=20
total work=51 average work per push=2.55
capacity growth: 1 2 4 8 16 32
```

测试还插入 1000 个元素，断言复制次数小于 `2n`，总工作量小于 `3n`，并检查容量始终为 2 的幂。

## 正确性思路

容量增长到 `2^k` 前的复制规模是 `1+2+4+...+2^{k-1}=2^k-1`。若最终存放 `n` 个元素，则最终容量小于 `2n`，所以复制总量小于 `2n`。每次插入还写入一个新元素，`n` 次插入总写入为 `n`。因此 `n` 次 `push_back` 的总成本小于常数倍的 `n`。

## 常见错误

- 把均摊 `O(1)` 理解成每次操作都很快；扩容那一次仍然可能很贵。
- 容量每次只增加 1，这会让总复制量变成 `1+2+...+n`。
- 只讨论时间，不讨论扩容时旧数组和新数组并存带来的内存峰值。

## 练习

1. 把扩容因子改成 1.5，比较复制总量和空闲容量。
2. 模拟容量加 1 的策略，观察总工作量曲线。
3. 加入 `pop_back` 和缩容策略，避免扩容/缩容抖动。
4. 用势能法重新证明相同结论。

## 参考资料

- [Princeton Algorithms: Stacks and Queues](https://algs4.cs.princeton.edu/13stacks/)
- [MIT OCW 6.006: Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
{% endraw %}
