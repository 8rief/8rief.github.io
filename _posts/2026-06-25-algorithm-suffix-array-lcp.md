---
layout: post
title: "后缀数组和 LCP：把字符串后缀排成可二分的索引"
date: 2026-06-25 15:44:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用倍增排序构建后缀数组，用 Kasai 算法构建 LCP，并通过 banana 和随机字符串对照朴素排序。"
tags: [algorithm, suffix-array, lcp, string, cplusplus]
---
{% raw %}
> 主题：Suffix Array / LCP / String Indexing / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

后缀数组把字符串的所有后缀按字典序排列，并保存每个后缀的起始位置。LCP 数组记录相邻后缀的最长公共前缀长度。二者结合后，字符串匹配、最长重复子串、后缀相邻关系都可以转化为数组问题。

## 学习目标

1. 理解 `sa[i]` 表示第 `i` 小后缀的起点。
2. 用倍增 rank 排序长度逐渐翻倍的前缀。
3. 用 Kasai 算法线性构建 LCP。
4. 用朴素后缀排序验证实现。
5. 说明 SA 与 Trie、Aho-Corasick 的适用差异。

## 核心模型

![后缀数组和 LCP](/assets/diagrams/algorithm-suffix-array-lcp.svg)

长度为 `2k` 的前缀可以拆成两个长度为 `k` 的 rank 对。每轮排序都把已知比较长度翻倍，直到 rank 唯一。

## C++ 实现片段

```cpp
for (int k = 1;; k <<= 1) {
    auto key = [&](int i) {
        return std::pair<int,int>{rank[i], i + k < n ? rank[i + k] : -1};
    };
    std::sort(sa.begin(), sa.end(), [&](int a, int b) {
        return key(a) < key(b);
    });
    tmp[sa[0]] = 0;
    for (int i = 1; i < n; ++i) {
        tmp[sa[i]] = tmp[sa[i - 1]] + (key(sa[i - 1]) < key(sa[i]));
    }
    rank = tmp;
    if (rank[sa.back()] == n - 1) break;
}
```

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
s=banana
sa: 5 3 1 0 4 2
lcp: 1 3 0 0 2
```

`banana` 的后缀顺序是 `a, ana, anana, banana, na, nana`。随机测试把倍增 SA 和 Kasai LCP 与朴素 `substr` 排序逐项对照。

## 正确性思路

第 `k` 轮后，rank 正确表示长度 `2^k` 前缀的字典序类别。下一轮比较两个 rank 组成的二元组，就能得到长度 `2^{k+1}` 的类别。Kasai 算法利用相邻起点公共前缀最多减少 1 的性质，把总比较次数限制在线性级别。

## 常见错误

- 第二段越界时没有使用哨兵 rank。
- 把 LCP 数组长度写成 `n`；相邻后缀只有 `n-1` 对。
- 直接在大输入上使用 `substr` 比较，导致隐藏的高复杂度。

## 练习

1. 用后缀数组查找模式串出现区间。
2. 用 LCP 求最长重复子串。
3. 把比较排序改成计数排序。
4. 对比后缀数组和后缀自动机。

## 参考资料

- [cp-algorithms: Suffix Array](https://cp-algorithms.com/string/suffix-array.html)
- [Princeton Algorithms: Substring Search](https://algs4.cs.princeton.edu/53substring/)
- [cppreference: std::sort](https://en.cppreference.com/w/cpp/algorithm/sort)
{% endraw %}
