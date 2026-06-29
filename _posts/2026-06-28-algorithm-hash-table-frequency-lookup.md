---
layout: post
title: "哈希表和哈希集合：去重、计数和快速查找的边界"
date: 2026-06-28 21:41:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从词频统计、首个重复值和 two-sum lookup 讲清 unordered_map/unordered_set 的实用模型。"
tags: [algorithm, hash-table, unordered-map, cpp, lookup]
---
{% raw %}

> 主题：算法实用基础 / hash table / frequency / lookup  
> 本文 lab 已验证：词频中 `api=3`、`db=2`，首个重复字符串是 `api`。

很多开发问题需要快速回答“这个值之前见过吗”“这个键出现了几次”“是否存在另一个数能和当前数凑成目标”。排序能解决一部分问题，但排序会改变顺序，并带来 `O(n log n)` 成本。哈希表适合把值映射到计数、位置或状态，让平均查找接近 `O(1)`。

## 问题模型

输入是一组键，例如字符串、整数或结构化对象。目标是在遍历过程中维护从键到信息的映射：出现次数、首次位置、是否访问过。哈希集合只关心键是否存在；哈希表还保存键对应的值。

## 核心不变量

![哈希表查找不变量](/assets/diagrams/algorithm-hash-table-frequency-lookup.svg)

处理到第 i 个元素前，哈希表保存前 i 个元素已经形成的事实。词频表保存每个词出现次数；visited 集合保存已经见过的值；two-sum 表保存某个数第一次出现的位置。每处理一个新元素，先用已有事实回答问题，再把新事实写入表。

## 正确性理由

以 two-sum 为例。遍历到 `values[i]` 时，如果 `target - values[i]` 已经在表里，就找到了一对下标，并且左端点在当前元素之前。如果不在表里，把当前值和下标记录下来，不会漏掉未来以当前值为左端点的答案。因为每个答案都有一个较早元素和一个较晚元素，较晚元素被处理时一定能查到较早元素。

## 复杂度分析

在哈希函数分布良好时，插入和查找的平均时间是 `O(1)`，遍历 n 个元素的总时间是 `O(n)`，空间是不同键数量 `O(m)`。最坏情况下可能退化，因此不要把哈希表当成无条件的性能保证；需要确定顺序或最坏界时，可以考虑 `map`、排序或其他结构。

## C++ 实现

词频统计：

```cpp
unordered_map<string, int> counts;
for (const string& word : words) {
    ++counts[word];
}
```

找首个重复值：

```cpp
optional<string> first_duplicate(const vector<string>& values) {
    unordered_set<string> seen;
    for (const string& value : values) {
        if (seen.count(value)) return value;
        seen.insert(value);
    }
    return nullopt;
}
```

two-sum 查询：

```cpp
optional<pair<int, int>> two_sum_indices(const vector<int>& values, int target) {
    unordered_map<int, int> first_index;
    for (int i = 0; i < static_cast<int>(values.size()); ++i) {
        int need = target - values[i];
        if (first_index.count(need)) return pair<int, int>{first_index[need], i};
        first_index.emplace(values[i], i);
    }
    return nullopt;
}
```

## 测试与边界

lab 验证了计数、重复值、two-sum 正例，还用暴力枚举和哈希写法做了正反两类对照：

```text
hash_first_duplicate=api
```

边界包括空数组、没有重复、目标不存在、重复值覆盖位置。文章中的实现用 `emplace` 保留第一次出现位置，这能让返回下标更稳定。

## 练习

1. 统计一组日志级别中 `INFO`、`WARN`、`ERROR` 的次数。
2. 写一个函数判断数组是否有重复值。
3. 把 two-sum 改成返回所有下标对，并与暴力枚举对照。

## 参考资料

- cppreference：[std::unordered_map](https://en.cppreference.com/w/cpp/container/unordered_map)
- cppreference：[std::unordered_set](https://en.cppreference.com/w/cpp/container/unordered_set)
- cppreference：[Hash policy](https://en.cppreference.com/w/cpp/container/unordered_map/rehash)

{% endraw %}
