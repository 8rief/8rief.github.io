---
layout: post
title: "堆和优先队列：把“每次取最重要元素”写成稳定模型"
date: 2026-06-28 21:40:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用 top-k 和任务调度讲清堆的不变量、priority_queue 的比较规则和 O(log n) 更新成本。"
tags: [algorithm, heap, priority-queue, cpp, invariant]
---
{% raw %}

> 主题：算法实用基础 / heap / priority queue / top-k  
> 本文 lab 已验证：`top_k_largest` 得到 `9,8,7`，任务调度输出按优先级稳定排序。

很多问题都可以描述成“每一步取当前最重要的元素”：日志里找最大的 k 个耗时、任务调度按优先级执行、Dijkstra 每次取当前距离最小的点。如果每次都排序，代价会很高。堆的作用是维护一个局部有序结构，让“取最值”和“插入新候选”都保持可控。

## 问题模型

输入是一组动态变化的元素，每个元素有一个可比较的优先级。需要支持两类操作：插入一个元素，取出当前最高或最低优先级元素。top-k 问题可以转化为维护一个大小不超过 k 的小根堆：堆里始终保存目前看到的 k 个最大值。

## 核心不变量

![堆和优先队列不变量](/assets/diagrams/algorithm-heap-priority-queue-topk.svg)

小根堆的不变量是：堆顶是当前堆中最小的元素。维护 top-k 最大值时，堆的大小最多是 k；如果新元素进入后大小超过 k，就弹出堆顶。弹出的正是当前 k+1 个候选中最小的元素，剩下的 k 个就是目前最大的 k 个。

## 正确性理由

按输入顺序处理元素。处理到第 i 个元素后，堆中保存前 i 个元素中的 k 个最大值。初始为空成立。加入新元素后，堆中临时有 k+1 个候选；弹出最小者后，任何被弹出的元素都不可能进入前 k 大，剩余元素仍是前 i 个元素中的 k 个最大值。归纳到最后，堆中就是全局 top-k。

## 复杂度分析

设输入长度为 n，k 是保留元素个数。每个元素最多一次入堆，一旦大小超过 k 就一次出堆。堆大小始终不超过 k，所以总时间是 `O(n log k)`，额外空间是 `O(k)`。如果直接排序，时间是 `O(n log n)`，当 k 远小于 n 时，堆更适合。

## C++ 实现

`std::priority_queue` 默认是大根堆。小根堆需要指定比较器：

```cpp
vector<int> top_k_largest(const vector<int>& values, int k) {
    priority_queue<int, vector<int>, greater<int>> heap;
    for (int value : values) {
        heap.push(value);
        if (static_cast<int>(heap.size()) > k) heap.pop();
    }
    vector<int> result;
    while (!heap.empty()) {
        result.push_back(heap.top());
        heap.pop();
    }
    sort(result.begin(), result.end(), greater<int>());
    return result;
}
```

任务调度可以用大根堆。lab 中把 `task_id` 存成负数，是为了在相同优先级下让较小编号先出队：

```cpp
priority_queue<pair<int, int>> pq;
for (auto [priority, task_id] : tasks) {
    pq.push({priority, -task_id});
}
```

## 测试与边界

本地 lab 验证了三个边界：普通 top-k、`k = 0`、相同优先级下的任务顺序。

```text
heap_top3=9,8,7
```

需要额外注意：`priority_queue` 只能直接访问堆顶，不能高效删除中间任意元素。如果问题需要“删除指定 id”或“修改优先级”，常见做法是惰性删除，或者换成 `set`、可索引堆等结构。

## 练习

1. 把 `top_k_largest` 改成保留最小的 k 个数。
2. 为任务调度增加 `created_at`，在优先级相同时先执行更早创建的任务。
3. 用堆合并 k 个有序数组，分析复杂度。

## 参考资料

- cppreference：[std::priority_queue](https://en.cppreference.com/w/cpp/container/priority_queue)
- cppreference：[std::make_heap](https://en.cppreference.com/w/cpp/algorithm/make_heap)
- CP-Algorithms：[Dijkstra and priority queue usage](https://cp-algorithms.com/graph/dijkstra_sparse.html)

{% endraw %}
