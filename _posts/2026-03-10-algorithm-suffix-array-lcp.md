---
layout: post
title: "后缀数组和 LCP：把字符串后缀排成可二分的索引"
date: 2026-03-10 09:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用倍增排序构建后缀数组，用 Kasai 算法构建 LCP，并通过 banana 和随机字符串对照朴素排序。"
tags: [algorithm, suffix-array, lcp, string, cplusplus]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithms-suffix-array-lcp/README.md`](/assets/labs/algorithms-suffix-array-lcp/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：Suffix Array / LCP / String Indexing / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

后缀数组把字符串的所有后缀按字典序排列，并保存每个后缀的起始位置。LCP 数组记录相邻后缀的最长公共前缀长度。二者结合后，字符串匹配、最长重复子串、后缀相邻关系都可以转化为数组问题。

直接保存 n 个后缀字符串会复制 `Θ(n²)` 个字符。后缀数组只保存 n 个起点，通过排序后的邻接关系复用原字符串，是一种紧凑的静态全文索引。

## 学习目标

1. 理解 `sa[i]` 表示第 `i` 小后缀的起点。
2. 用倍增 rank 排序长度逐渐翻倍的前缀。
3. 用 Kasai 算法线性构建 LCP。
4. 用朴素后缀排序验证实现。
5. 说明 SA 与 Trie、Aho-Corasick 的适用差异。

## 核心模型

![后缀数组和 LCP](/assets/diagrams/algorithm-suffix-array-lcp.svg)

长度为 `2k` 的前缀可以拆成两个长度为 `k` 的 rank 对。每轮排序都把已知比较长度翻倍，直到 rank 唯一。

## 为什么要引入 rank 倍增

直接比较两个后缀最坏要扫描 `O(n)` 个字符；比较排序做 `O(n log n)` 次比较，容易达到 `O(n² log n)`。倍增算法把已知长度 k 的字典序类别压成整数 rank，下一轮只比较：

```text
(rank[i], rank[i+k])
```

于是每次比较为常数时间，已知前缀长度从 1、2、4、8 逐轮翻倍。

当前实现每轮用 `std::sort`，总复杂度为 `O(n log²n)`；若对整数 rank 使用计数排序，可优化到 `O(n log n)`。

## `banana` 的完整后缀表

| 起点 | 后缀 |
| ---: | --- |
| 0 | banana |
| 1 | anana |
| 2 | nana |
| 3 | ana |
| 4 | na |
| 5 | a |

字典序排序后起点是 `5,3,1,0,4,2`。

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

越界的第二段 rank 使用 -1，它比任何真实字符 rank 小，因此较短且前缀相同的后缀排在前面。循环在最后一个后缀 rank 达到 `n-1` 时结束，表示所有 rank 唯一。

## LCP 每一项怎样得到

LCP 数组长度为 `n-1`，第 i 项对应 `suffix(sa[i])` 与 `suffix(sa[i+1])`：

```text
a      / ana    -> 1
ana    / anana  -> 3
anana  / banana -> 0
banana / na     -> 0
na     / nana   -> 2
```

因此输出为 `1,3,0,0,2`，最大值 3 对应重复子串 `ana`。

Kasai 构建先计算逆 rank，再按原起点 i 扫描：

```cpp
int h = 0;
for (int i = 0; i < n; ++i) {
    if (rank[i] == n - 1) { h = 0; continue; }
    int j = sa[rank[i] + 1];
    while (i+h < n && j+h < n && s[i+h] == s[j+h]) ++h;
    lcp[rank[i]] = h;
    if (h) --h;
}
```

起点从 i 移到 i+1 后，上一轮公共前缀去掉第一个字符，仍提供至少 `h-1` 的可复用下界；h 每次最多减少 1，总字符比较为 `O(n)`。

## 实验输出怎样解释

```text
100% tests passed, 0 tests failed out of 1
s=banana
sa: 5 3 1 0 4 2
lcp: 1 3 0 0 2
```

`banana` 的后缀顺序是 `a, ana, anana, banana, na, nana`。随机测试把倍增 SA 和 Kasai LCP 与朴素 `substr` 排序逐项对照。

复跑：

```bash
./run_lab.sh
```

CTest 还使用 seed 9 生成 500 个长度 1 到 35、字符集 `{a,b,c,d}` 的随机字符串，同时对照朴素 SA 和朴素 LCP。lab 已增加空字符串断言，公开函数对空输入返回空数组。

## 正确性思路

第 `k` 轮后，rank 正确表示长度 `2^k` 前缀的字典序类别。下一轮比较两个 rank 组成的二元组，就能得到长度 `2^{k+1}` 的类别。Kasai 算法利用相邻起点公共前缀最多减少 1 的性质，把总比较次数限制在线性级别。

构建后可对模式串与 `suffix(sa[mid])` 做二分，找到匹配后缀的连续区间。若每次比较最多扫描模式长度 m，查询为 `O(m log n)`；结合 LCP 或更细索引还能减少重复字符比较。

## 常见错误

- 第二段越界时没有使用哨兵 rank。
- 把 LCP 数组长度写成 `n`；相邻后缀只有 `n-1` 对。
- 直接在大输入上使用 `substr` 比较，导致隐藏的高复杂度。
- 忘记空字符串边界；没有提前返回时会访问 `sa[0]`。
- 把 LCP 最大值的位置直接当字符串起点；需要通过相邻的 `sa` 项还原后缀。
- 混淆“后缀排序”和“所有子串排序”；后缀数组保存的只有 n 个后缀起点。

## 练习

1. 用后缀数组查找模式串出现区间。
2. 用 LCP 求最长重复子串。
3. 把比较排序改成计数排序。
4. 对比后缀数组和后缀自动机。
5. 输出 `banana` 的最长重复子串及其两个起点，并用 LCP 最大项验证。

## 参考资料

- [cp-algorithms: Suffix Array](https://cp-algorithms.com/string/suffix-array.html)
- [Princeton Algorithms: Substring Search](https://algs4.cs.princeton.edu/53substring/)
- [cppreference: std::sort](https://en.cppreference.com/w/cpp/algorithm/sort)
{% endraw %}
