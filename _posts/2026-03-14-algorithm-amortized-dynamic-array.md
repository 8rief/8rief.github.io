---
layout: post
title: "摊还分析：动态数组扩容为什么均摊 O(1)"
date: 2026-03-14 09:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用动态数组倍增扩容实验解释聚合分析：单次扩容可能很贵，但连续 push 的总复制次数受几何级数限制。"
tags: [algorithm, amortized-analysis, dynamic-array, cplusplus]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithms-amortized-dynamic-array/README.md`](/assets/labs/algorithms-amortized-dynamic-array/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：Amortized Analysis / Dynamic Array / 聚合分析 / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

动态数组的 `push_back` 有时只写入一个元素，有时会触发扩容并复制全部旧元素。单次最坏复杂度可能达到 `O(n)`，但连续执行很多次插入时，倍增扩容的总成本仍是线性的。摊还分析研究的正是这种“局部峰值高、整体平均低”的操作序列。

均摊复杂度不是基于随机输入的平均值。它对任意长度为 n 的合法操作序列给出总成本上界，再把总成本分摊到每次操作。

## 学习目标

1. 区分单次最坏复杂度和均摊复杂度。
2. 用聚合分析证明倍增扩容的复制总量小于线性上界。
3. 写出可记录复制次数、写入次数和容量轨迹的模型。
4. 说明按 1 增长容量为什么会退化。
5. 用实验输出解释均摊 `O(1)` 的含义。

## 核心模型

![动态数组摊还分析](/assets/diagrams/algorithm-amortized-dynamic-array.svg)

倍增扩容的容量轨迹是 `1,2,4,8,...`。复制旧元素的总数是一个几何级数；插入 `n` 个元素时，扩容复制总量小于 `2n`，再加上 `n` 次新元素写入，总工作量仍是 `O(n)`。

## 为什么要引入摊还分析

只看单次最坏情况会得到 `push_back=O(n)`，却无法解释长序列为何仍高效；只取实验平均值又无法提供输入无关保证。聚合分析直接研究前 n 次操作的总工作量：

```text
amortized cost = total cost of operation sequence / number of operations
```

它允许某次扩容很贵，只要这种昂贵操作出现得足够稀疏。

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

当前类是一个可观察成本的教学模型：每复制一个旧整数记 1 单位，每写入一个新整数也记 1 单位。真实 `std::vector` 的分配器、对象移动/复制和异常安全成本更复杂，而且 C++ 标准不规定实现必须按 2 倍扩容；标准接口提供的是相应的摊还复杂度约束。

## 实验输出怎样解释

```text
100% tests passed, 0 tests failed out of 1
after 20 pushes: size=20 capacity=32 copied=31 writes=20
total work=51 average work per push=2.55
capacity growth: 1 2 4 8 16 32
```

测试还插入 1000 个元素，断言复制次数小于 `2n`，总工作量小于 `3n`，并检查容量始终为 2 的幂。

20 次插入中，扩容复制量为：

```text
0 + 1 + 2 + 4 + 8 + 16 = 31
```

初次从容量 0 增到 1 时没有旧元素可复制。再加 20 次新元素写入，总工作量是 51，均摊为 `51/20=2.55`。

复跑：

```bash
./run_lab.sh
```

固定测试还检查 17 次插入时容量轨迹恰为 `1,2,4,8,16,32`、复制次数为 31；1000 次测试逐项确认存入的 `i²` 没有在扩容中丢失。

## 正确性思路

容量增长到 `2^k` 前的复制规模是 `1+2+4+...+2^{k-1}=2^k-1`。若最终存放 `n` 个元素，则最终容量小于 `2n`，所以复制总量小于 `2n`。每次插入还写入一个新元素，`n` 次插入总写入为 `n`。因此 `n` 次 `push_back` 的总成本小于常数倍的 `n`。

更精确地说，最终容量 C 是不小于 n 的最小二次幂，因此 `C<2n`；历次复制总量为 `C-1<2n`，总工作量小于 `3n`。于是每次操作的均摊工作量严格小于 3 个模型单位。

## 为什么容量加 1 会退化

若每满一次只增加一个槽，第 i 次扩容要复制 i 个元素：

```text
0+1+2+...+(n-1) = n(n-1)/2 = Θ(n²)
```

n 次 push 的均摊成本变成 `Θ(n)`。使用固定比例 `α>1` 扩容会形成几何级数；α 越接近 1，空闲空间少但复制更频繁，体现时间与内存的权衡。

## 与势能法的关系

也可以把未使用容量看成为未来扩容预存的势能。普通插入支付常数费用，部分费用积累；扩容时释放已积累势能支付复制。聚合分析和势能法给出同一渐近结论，后者更适合插入、删除混合的操作序列。

## 常见错误

- 把均摊 `O(1)` 理解成每次操作都很快；扩容那一次仍然可能很贵。
- 容量每次只增加 1，这会让总复制量变成 `1+2+...+n`。
- 只讨论时间，不讨论扩容时旧数组和新数组并存带来的内存峰值。
- 把实验中的 2 倍策略当作所有 `std::vector` 实现的固定规则。
- 直接把均摊界当延迟上界；实时系统仍需考虑某次重分配的峰值。

## 练习

1. 把扩容因子改成 1.5，比较复制总量和空闲容量。
2. 模拟容量加 1 的策略，观察总工作量曲线。
3. 加入 `pop_back` 和缩容策略，避免扩容/缩容抖动。
4. 用势能法重新证明相同结论。
5. 记录 1.25、1.5、2.0 三种扩容因子的复制量、最终空闲容量和峰值内存。

## 参考资料

- [Princeton Algorithms: Stacks and Queues](https://algs4.cs.princeton.edu/13stacks/)
- [MIT OCW 6.006: Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
{% endraw %}
