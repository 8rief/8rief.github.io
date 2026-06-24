---
layout: post
title: "KMP 字符串匹配：prefix function 如何避免回头重比"
date: 2026-06-25 05:40:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用 prefix function 解释 KMP 的失配跳转、线性复杂度和重叠匹配，并用随机字符串对照朴素搜索。"
tags: [algorithm, string, kmp, prefix-function, cplusplus]
---
{% raw %}

> 主题：字符串算法 / KMP / prefix function / C++ 可复现实验  
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含固定样例、重叠匹配和随机朴素搜索对照。

字符串匹配的朴素做法会在失配后把模式串整体右移一位，然后从头比较。KMP 的核心问题是：已经比较过的字符能不能复用？prefix function 给出的答案是：当模式串前缀和当前后缀相等时，失配后可以跳到最长可复用边界，而不必回到 0。

这篇文章只讲 prefix-function 版本的 KMP。它足够短，也能直接连接到后续的 Z 函数、字符串哈希、Trie 和自动机。

## 学习目标

1. 定义 prefix function `pi[i]` 的含义。
2. 写出失配时 `j = pi[j - 1]` 的跳转逻辑。
3. 支持重叠匹配，例如在 `aaaa` 中找 `aa`。
4. 证明每个字符的比较次数是线性级别。
5. 用朴素搜索验证 KMP 输出位置。

## 核心模型

![KMP prefix function](/assets/diagrams/algorithm-kmp-prefix-function.svg)

`pi[i]` 表示 `s[0..i]` 的最长真前缀长度，使这个前缀同时也是后缀。匹配过程中，`j` 表示当前已经匹配的模式串长度。失配时，KMP 不移动文本指针，只把 `j` 跳到下一个可能的前后缀边界。

## prefix function

```cpp
std::vector<int> prefix_function(const std::string& s) {
    std::vector<int> pi(s.size(), 0);
    for (std::size_t i = 1; i < s.size(); ++i) {
        int j = pi[i - 1];
        while (j > 0 && s[i] != s[j]) j = pi[j - 1];
        if (s[i] == s[j]) ++j;
        pi[i] = j;
    }
    return pi;
}
```

`j` 从上一位置的最长边界开始尝试。如果当前字符不能延长这个边界，就继续跳到更短边界，直到能匹配或归零。

## KMP 搜索

```cpp
std::vector<int> kmp_search(const std::string& text,
                            const std::string& pattern) {
    auto pi = prefix_function(pattern);
    std::vector<int> pos;
    int j = 0;
    for (int i = 0; i < static_cast<int>(text.size()); ++i) {
        while (j > 0 && text[i] != pattern[j]) j = pi[j - 1];
        if (text[i] == pattern[j]) ++j;
        if (j == static_cast<int>(pattern.size())) {
            pos.push_back(i - j + 1);
            j = pi[j - 1];
        }
    }
    return pos;
}
```

找到一次匹配后，把 `j` 设为 `pi[j - 1]`，可以继续寻找重叠匹配。比如 `aaaa` 中的 `aa` 出现在位置 `0、1、2`。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
prefix function for ababaca: 0 0 1 2 3 0 1
positions of aba in ababaababaca: 0 2 5 7
```

测试包含 `ababaca` 的 prefix function、`aaaa` 中 `aa` 的重叠匹配，以及 500 轮随机小字母表字符串。KMP 输出位置必须和朴素 `substr` 搜索完全一致。

## 正确性思路

当 `pattern[0..j-1]` 已经匹配文本后缀，而下一个字符失配时，任何可行的新匹配都必须是这个已匹配串的某个后缀，同时也是模式串前缀。`pi[j-1]` 正好给出最长这样的边界；如果仍不匹配，就继续沿 prefix function 链向更短边界跳转。

每次文本指针 `i` 只前进，`j` 虽然会回退，但总回退次数受此前增加次数限制。因此整体是 `O(n + m)`。

## 复杂度

- 计算 prefix function：`O(m)`。
- 搜索长度为 `n` 的文本：`O(n)`。
- 总时间：`O(n + m)`，额外空间 `O(m)`。

## 常见错误

**匹配后把 j 清零。** 这样会漏掉重叠匹配。应该跳到 `pi[j - 1]`。

**空模式串语义不明。** 工程接口要明确空模式返回什么。实验代码选择返回空位置集合。

**把 pi 理解成出现次数。** `pi[i]` 表示边界长度；前缀出现次数需要另外统计。

## 练习

1. 打印 KMP 每次失配时 `j` 的跳转链。
2. 用 `pattern + '#' + text` 的 prefix function 写另一种匹配版本。
3. 统计每个前缀在字符串中出现的次数。
4. 比较 KMP 和字符串哈希在多模式、多查询场景下的取舍。

## 参考资料

- [cp-algorithms: Prefix function](https://cp-algorithms.com/string/prefix-function.html)
- [Princeton Algorithms, Part II](https://algs4.cs.princeton.edu/home/i)
- [cppreference: std::string](https://en.cppreference.com/w/cpp/string/basic_string)
{% endraw %}
