---
layout: post
title: "动态规划入门：先定义状态，再决定转移顺序"
date: 2026-03-07 18:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用 0/1 背包和 LIS 说明动态规划的状态、转移、遍历顺序和压缩空间，并用暴力模型验证结果。"
tags: [algorithm, dynamic-programming, knapsack, lis, cplusplus]
---
{% raw %}

> 主题：动态规划 / 状态定义 / 0/1 背包 / 最长上升子序列 / C++ 可复现实验  
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验用暴力枚举和 `O(n^2)` LIS 对照验证。

动态规划的核心是把重复子问题组织成状态图。写 DP 之前先问三个问题：状态表示什么？状态从哪些更小状态转移？按什么顺序计算才能保证依赖已经就绪？

本文用两个代表例子：0/1 背包体现“选择或不选择”的状态转移和倒序压缩；LIS 体现“维护最优尾值”的另一种 DP 视角。一个偏组合选择，一个偏序列结构，放在一起能避免把 DP 简化成二维数组填表。

## 为什么需要先定义状态

同一条转移式在不同状态语义下可能完全错误。`dp[c]` 可以表示“容量恰好为 c”或“容量不超过 c”，两者的初始化和不可达状态不同；容量正序或倒序又决定当前物品能否被重复使用。

可靠的顺序是先写一句可验证的状态定义，再列出转移来自哪些旧状态，最后根据依赖关系安排循环。空间压缩应放在二维版本已经正确之后，因为它会把“上一轮”和“当前轮”复用到同一数组。

## 学习目标

1. 用一句话定义 DP 状态。
2. 写出 0/1 背包的一维压缩转移。
3. 解释为什么 0/1 背包容量要倒序遍历。
4. 写出 `O(n log n)` LIS 的尾值数组含义。
5. 用暴力或慢算法验证 DP 输出。

## 核心模型

![动态规划状态和转移](/assets/diagrams/algorithm-dynamic-programming-core.svg)

DP 的核心是有向无环的依赖关系，数组只是保存状态值的容器。计算某个状态前，它依赖的状态必须已经计算好。背包的一维压缩通过倒序遍历容量，避免同一件物品在同一轮被重复使用。

## 0/1 背包

状态定义：处理完当前若干物品后，`dp[c]` 表示容量不超过 `c` 时可获得的最大价值。

```cpp
int knapsack_01(const std::vector<int>& weight,
                const std::vector<int>& value,
                int capacity) {
    std::vector<int> dp(capacity + 1, 0);
    for (std::size_t i = 0; i < weight.size(); ++i) {
        for (int c = capacity; c >= weight[i]; --c) {
            dp[c] = std::max(dp[c], dp[c - weight[i]] + value[i]);
        }
    }
    return dp[capacity];
}
```

容量倒序是关键。如果正序遍历，`dp[c - weight[i]]` 可能已经使用了第 `i` 个物品，当前转移会把同一物品重复选多次，变成完全背包语义。

固定样例容量为 5，物品依次是 `(重量,价值)=(2,3),(3,4),(4,5),(5,8)`。每处理一件物品后的 `dp[0..5]` 为：

```text
初始:      0 0 0 0 0 0
加入(2,3): 0 0 3 3 3 3
加入(3,4): 0 0 3 4 4 7
加入(4,5): 0 0 3 4 5 7
加入(5,8): 0 0 3 4 5 8
```

最后选择重量 5、价值 8 的单件物品。若容量正序，处理 `(2,3)` 时刚写出的 `dp[2]=3` 会立即参与 `dp[4]`，相当于同一件物品用了两次。

## LIS：最长上升子序列

`tail[len - 1]` 表示长度为 `len` 的上升子序列中，最小可能结尾值。结尾越小，后面越容易接上新元素。

```cpp
int lis_length(const std::vector<int>& a) {
    std::vector<int> tail;
    for (int x : a) {
        auto it = std::lower_bound(tail.begin(), tail.end(), x);
        if (it == tail.end()) tail.push_back(x);
        else *it = x;
    }
    return static_cast<int>(tail.size());
}
```

`tail` 保存的是每个长度下最有扩展潜力的结尾值，不承诺自身就是某个真实子序列的完整内容。使用 `lower_bound` 对应严格上升；如果要求非下降子序列，需要改成 `upper_bound`。

样例 `[10,9,2,5,3,7,101,18]` 的 tail 变化为：

```text
10  -> [10]
9   -> [9]
2   -> [2]
5   -> [2,5]
3   -> [2,3]
7   -> [2,3,7]
101 -> [2,3,7,101]
18  -> [2,3,7,18]
```

最终长度为 4。最后一次把 101 替换为 18 没有缩短已有解，只为后续元素留下更容易扩展的结尾。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
0/1 knapsack best value=8
LIS length=4
state design: dp[c] means best value using processed items under capacity c
```

测试使用 seed `20260625`。背包执行 300 轮，随机生成 0 到 16 件物品、容量 0 到 40，用枚举全部子集作为 oracle；LIS 再执行 300 轮，数组长度 0 到 16、值域 -10 到 10，用 `O(n²)` DP 作为 oracle。DP 代码经常在遍历顺序、空输入和重复值上出错，用慢但直接的模型对照更容易定位问题。

## 正确性思路

背包转移覆盖了每件物品的两种选择：不选时保持 `dp[c]`，选时来自旧状态 `dp[c - w[i]] + v[i]`。倒序遍历保证“旧状态”仍然是未使用当前物品的上一轮状态。

LIS 的正确性来自贪心维护：对于同样长度的上升子序列，较小结尾不会比更大结尾差。每个新元素替换第一个大于等于它的位置，保持所有长度的最小结尾。

## 复杂度

- 0/1 背包：`O(nC)` 时间、`O(C)` 空间，其中 `C` 是容量。
- LIS：`O(n log n)` 时间、`O(n)` 空间。

背包中的 C 是数值容量，因此这是伪多项式复杂度：输入只需 `log C` 位表示容量，运行时间却与 C 本身成正比。容量极大时，需要按价值做 DP、meet-in-the-middle 或问题特定优化。

## 输入和结果边界

- 教学版背包假设 capacity 非负、重量为正、weight 和 value 等长。公共接口应显式验证这些前置条件。
- 当前初始化适用于“容量不超过 c、允许不选物品、价值非负”的语义；若要求恰好装满，要用不可达标记区分 0。
- 空数组的 LIS 长度为 0；重复元素不会延长严格上升序列。
- `tail` 只能直接给出长度。恢复具体 LIS 需要保存每个元素的前驱和每个长度对应的末尾下标。

## 常见错误

**状态定义不清。** 如果不能用一句话解释 `dp[i][j]` 或 `dp[c]` 表示什么，转移式很容易只是猜出来的。

**压缩空间后遍历顺序错误。** 0/1 背包倒序，完全背包正序，原因来自是否允许同一轮重复使用当前物品。

**把 LIS 的 tail 当成答案序列。** 它用于求长度；要恢复具体序列，需要额外记录前驱。

**忽略容量的数值规模。** `O(nC)` 在 C 很大时不可行，即使物品数不多。

## 练习

1. 把 0/1 背包改成二维 DP，并打印表格。
2. 写完全背包，比较容量遍历方向。
3. 恢复 LIS 的一个具体序列。
4. 用 DAG 最长路径重新解释 DP 的计算顺序。

## 参考资料

- [MIT 6.006 Dynamic Programming lecture](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-19-dynamic-programming-i-fibonacci-shortest-paths/)
- [cp-algorithms: Introduction to Dynamic Programming](https://cp-algorithms.com/dynamic_programming/intro-to-dp.html)
- [cppreference: std::lower_bound](https://en.cppreference.com/w/cpp/algorithm/lower_bound)
{% endraw %}
