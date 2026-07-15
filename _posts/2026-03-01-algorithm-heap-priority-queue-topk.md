---
layout: post
title: "堆和优先队列：把“每次取最重要元素”写成稳定模型"
date: 2026-03-01 09:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用 top-k 和任务调度讲清堆的不变量、priority_queue 的比较规则和 O(log n) 更新成本。"
tags: [algorithm, heap, priority-queue, cpp, invariant]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithm-practical-foundations/README.md`](/assets/labs/algorithm-practical-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：算法实用基础 / heap / priority queue / top-k  
> 本文 lab 已验证：`top_k_largest` 得到 `9,8,7`，任务调度按优先级和显式 task-id 规则确定顺序。

很多问题都可以描述成“每一步取当前最重要的元素”：日志里找最大的 k 个耗时、任务调度按优先级执行、Dijkstra 每次取当前距离最小的点。如果每次都排序，代价会很高。堆的作用是维护一个局部有序结构，让“取最值”和“插入新候选”都保持可控。

流式数据尤其适合这个模型：数据持续到达时，完整排序要求保存全部元素并在末尾处理；大小为 k 的堆可以随到随处理，内存只随 k 增长。

## 问题模型

输入是一组动态变化的元素，每个元素有一个可比较的优先级。需要支持两类操作：插入一个元素，取出当前最高或最低优先级元素。top-k 问题可以转化为维护一个大小不超过 k 的小根堆：堆里始终保存目前看到的 k 个最大值。

## 为什么要引入堆

排序维护了所有元素之间的完整顺序，而“反复取当前最值”只需要知道堆顶。二叉堆用一棵近似完全二叉树保存较弱的不变量：

```text
小根堆：parent <= children
大根堆：parent >= children
```

它不保证左右兄弟或同层元素有序。弱化顺序后，堆顶访问为 `O(1)`，插入和弹出只需沿一条根叶路径调整，为 `O(log n)`。

二叉堆通常存进连续数组。0-based 下标中：

```text
parent(i) = (i-1)/2
left(i)   = 2i+1
right(i)  = 2i+2
```

因此无需为树节点保存指针。

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
    if (k < 0) throw invalid_argument("k must be non-negative");
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

`greater<int>` 使最小元素位于堆顶。若 `k=0`，每次 push 后立即 pop，最终返回空数组；若 `k>n`，函数返回全部元素的降序结果。重复值按出现次数保留，例如两个 7 可以同时进入 top-k。

## top-3 状态轨迹

输入为 `4,1,7,7,3,9,2,8`，堆内集合按升序展示如下：

| 读入 | 超过 3 时弹出 | 保留集合 |
| ---: | ---: | --- |
| 4 | — | 4 |
| 1 | — | 1,4 |
| 7 | — | 1,4,7 |
| 7 | 1 | 4,7,7 |
| 3 | 3 | 4,7,7 |
| 9 | 4 | 7,7,9 |
| 2 | 2 | 7,7,9 |
| 8 | 7 | 7,8,9 |

最后把三个堆元素取出并降序整理，得到 `9,8,7`。堆内部数组本身不保证打印为排序结果，所以展示前单独排序。

任务调度可以用大根堆。lab 中把 `task_id` 存成负数，是为了在相同优先级下让较小编号先出队：

```cpp
priority_queue<pair<int, int>> pq;
for (auto [priority, task_id] : tasks) {
    pq.push({priority, -task_id});
}
```

`std::pair` 按 first、再按 second 做字典序比较。保存 `(priority,-task_id)` 后，优先级大的先出；优先级相同，`-task_id` 较大的对应原 task id 较小。该顺序来自显式 tie-break，不是容器的稳定性保证。

## 测试输出怎样解释

本地 lab 验证了三个边界：普通 top-k、`k = 0`、相同优先级下的任务顺序。

```text
tests_passed=30
heap_top3=9,8,7
```

`tests_passed=30` 是整个算法实用基础 lab 的总测试数；其中与本文直接相关的是三项 heap 断言。任务样例 `{{2,10},{5,11},{5,3},{1,7}}` 的预期顺序为 `3,11,10,7`。

复跑：

```bash
./run_lab.sh
```

需要额外注意：`priority_queue` 只能直接访问堆顶，不能高效删除中间任意元素。如果问题需要“删除指定 id”或“修改优先级”，常见做法是惰性删除，或者换成 `set`、可索引堆等结构。

## 复杂度边界

扫描 n 个元素需要 `O(n log k)`，把最终 k 个元素整理为降序还需 `O(k log k)`，空间为 `O(k)`。只需要无序 top-k 集合时可以省略最后排序。

当 `k` 接近 n 且必须完整有序时，直接排序更简单；当 k 远小于 n、输入流式到达或需要持续查询阈值时，小根堆更合适。

## 常见错误

1. 以为 `priority_queue` 的底层数组已经整体有序。
2. 维护 top-k 最大值却使用大根堆，导致弹出的是当前最大候选。
3. 没有定义相同优先级的 tie-break，输出顺序随输入或实现细节变化。
4. 忽略非法负 k；当前函数抛出 `invalid_argument`。
5. 用惰性删除却不清理已失效堆顶，查询返回旧状态。

## 练习

1. 把 `top_k_largest` 改成保留最小的 k 个数。
2. 为任务调度增加 `created_at`，在优先级相同时先执行更早创建的任务。
3. 用堆合并 k 个有序数组，分析复杂度。
4. 为 `top_k_largest` 增加随机数组测试，与完整排序后的前 k 项对照。

## 参考资料

- cppreference：[std::priority_queue](https://en.cppreference.com/w/cpp/container/priority_queue)
- cppreference：[std::make_heap](https://en.cppreference.com/w/cpp/algorithm/make_heap)
- CP-Algorithms：[Dijkstra and priority queue usage](https://cp-algorithms.com/graph/dijkstra_sparse.html)

{% endraw %}
