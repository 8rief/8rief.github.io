---
layout: post
title: "复杂度陷阱和边界测试：先估算会不会炸"
date: 2026-06-28 21:47:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用 O(n^2) 对数、邻接矩阵内存和暴力对照讲清算法实现前的规模判断。"
tags: [algorithm, complexity, testing, boundary, cpp]
---
{% raw %}

> 主题：算法实用基础 / complexity / boundary tests  
> 本文 lab 已验证：`n=100000` 的两两比较次数是 `4,999,950,000`。

算法代码写出来之前，先估算规模。很多超时或爆内存问题并不隐蔽：`n = 100000` 的两层循环已经接近 50 亿次；`20000 x 20000` 的邻接矩阵即使按 bool 粗略估算也会非常大。复杂度分析不是事后装饰，它应该在实现前筛掉错误路线。

## 问题模型

给定输入规模 n、图的点数 V 和边数 E、内存限制和时间限制，判断某个算法路线是否可行。然后为实现准备边界测试：空输入、极小输入、最大规模估算、随机小规模对照、异常结构。

## 核心不变量

![复杂度估算和边界测试闭环](/assets/diagrams/algorithm-complexity-traps-boundary-tests.svg)

实现前先估算数量级；实现后用小规模 oracle 对照；发布前用边界输入验证不会越界、不会递归爆栈、不会把稀疏图误建成稠密矩阵。这个闭环比单个样例通过更可靠。

## 正确性理由

边界测试不能证明算法完全正确，但能覆盖最容易犯错的输入形状。暴力对照适合小规模：慢算法逻辑直接，容易确认；快算法在同一批随机小输入上与暴力输出一致，可以快速发现漏边界、顺序错误和状态污染。

## 复杂度分析

两两比较次数是 `n(n-1)/2`。当 `n=100000` 时，次数为 `4,999,950,000`，通常不能放进普通在线评测的一秒级时间预算。邻接矩阵空间是 `O(V^2)`，邻接表空间是 `O(V+E)`。当图稀疏时，邻接表更接近真实边数。

## C++ 实现

估算两两比较次数：

```cpp
long long pair_count(long long n) {
    return n * (n - 1) / 2;
}
```

用暴力对照哈希 two-sum：

```cpp
vector<pair<int, int>> brute_force_pairs_with_sum(const vector<int>& values, int target) {
    vector<pair<int, int>> pairs;
    for (int i = 0; i < static_cast<int>(values.size()); ++i) {
        for (int j = i + 1; j < static_cast<int>(values.size()); ++j) {
            if (values[i] + values[j] == target) pairs.push_back({i, j});
        }
    }
    return pairs;
}
```

快算法和暴力算法只比较“是否存在答案”，避免把多个合法答案的下标顺序当成唯一标准。

## 测试与边界

lab 输出：

```text
pair_count_100000=4999950000
```

同时验证了哈希 two-sum 在正例和反例上与暴力枚举一致。对于图算法，还应测试孤立点、重边、自环、不连通图；对于 DP，应测试不可达状态、容量为 0、空数组；对于递归 DFS，应估计最大递归深度。

## 练习

1. 估算 `V=100000, E=200000` 时邻接表和邻接矩阵的空间差异。
2. 给 BFS 写一个随机小图生成器，用 Floyd-Warshall 或暴力层扩展对照。
3. 为 0/1 背包写暴力枚举 oracle，随机生成小规模用例。

## 参考资料

- cppreference：[std::mersenne_twister_engine](https://en.cppreference.com/w/cpp/numeric/random/mersenne_twister_engine)
- cppreference：[integer types](https://en.cppreference.com/w/cpp/types/integer)
- MIT 6.006：[Asymptotic notation](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/)

{% endraw %}
