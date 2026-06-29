---
layout: post
title: "基础 DP 题型：先写状态，再检查转移顺序"
date: 2026-06-28 21:44:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用零钱、0/1 背包和网格路径讲清一维 DP、二维 DP 与空间压缩的基本边界。"
tags: [algorithm, dynamic-programming, knapsack, cpp, testing]
---
{% raw %}

> 主题：算法实用基础 / dynamic programming / state transition  
> 本文 lab 已验证：`min_coins({1,3,4}, 6)=2`，容量 5 的 0/1 背包最优值为 9。

动态规划最容易学成“看到数组就填表”。更可靠的做法是先写清楚状态表示什么，再写从哪些旧状态转移，最后决定遍历顺序。本文只补基础题型：一维最短代价、0/1 背包、网格路径计数。

## 问题模型

DP 适合有重复子问题和最优子结构的问题。零钱问题问凑出金额 x 的最少硬币数；0/1 背包问容量 c 下的最大价值；网格路径问到达每个格子的路径数。它们都能把大问题拆成更小状态。

## 核心不变量

![基础 DP 状态和转移顺序](/assets/diagrams/algorithm-basic-dp-patterns.svg)

`dp[x]` 或 `dp[r][c]` 的值必须在被使用前已经正确计算。零钱问题按金额从小到大；0/1 背包压缩到一维后，容量必须倒序；网格路径按行列顺序计算，因为一个格子只依赖上方和左方。

## 正确性理由

零钱问题中，凑出金额 x 的最后一步一定使用某枚硬币 coin，所以前一个状态是 `x - coin`。枚举所有可用硬币并取最小值，就覆盖了所有可能的最后一步。背包问题中，每件物品只有选或不选两种选择；倒序遍历容量保证当前物品不会在同一轮被重复使用。网格路径中，到达一个格子只能来自上方或左方，因此两者路径数相加即可。

## 复杂度分析

零钱问题复杂度是 `O(amount * coin_count)`，空间是 `O(amount)`。0/1 背包复杂度是 `O(n * capacity)`，压缩后空间是 `O(capacity)`。R 行 C 列的网格路径复杂度是 `O(RC)`，空间可以从 `O(RC)` 压缩到 `O(C)`。

## C++ 实现

零钱最少硬币数：

```cpp
int min_coins(const vector<int>& coins, int amount) {
    const int inf = numeric_limits<int>::max() / 4;
    vector<int> dp(amount + 1, inf);
    dp[0] = 0;
    for (int x = 1; x <= amount; ++x) {
        for (int coin : coins) {
            if (x >= coin) dp[x] = min(dp[x], dp[x - coin] + 1);
        }
    }
    return dp[amount] >= inf ? -1 : dp[amount];
}
```

0/1 背包一维压缩：

```cpp
for (size_t i = 0; i < weights.size(); ++i) {
    for (int cap = capacity; cap >= weights[i]; --cap) {
        dp[cap] = max(dp[cap], dp[cap - weights[i]] + values[i]);
    }
}
```

网格路径遇到障碍时把状态清零：

```cpp
if (grid[r][c] == '#') dp[r][c] = 0;
else {
    if (r) dp[r][c] += dp[r - 1][c];
    if (c) dp[r][c] += dp[r][c - 1];
}
```

## 测试与边界

lab 输出：

```text
dp_min_coins_6=2 knapsack_capacity_5=9
```

测试覆盖了不可达金额、背包容量边界、障碍网格路径数。DP 的常见错误来自初始化、遍历方向和不可达状态。把小规模输入用暴力枚举对照，是定位 DP 错误的有效方法。

## 练习

1. 把零钱问题改成统计方案数，并说明遍历顺序变化。
2. 写二维 0/1 背包，再和一维压缩结果对照。
3. 给网格路径增加只能向右或向下走的路径恢复。

## 参考资料

- CP-Algorithms：[Introduction to Dynamic Programming](https://cp-algorithms.com/dynamic_programming/intro-to-dp.html)
- MIT 6.006：[Dynamic Programming I](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-19-dynamic-programming-i-fibonacci-shortest-paths/)
- cppreference：[std::numeric_limits](https://en.cppreference.com/w/cpp/types/numeric_limits)

{% endraw %}
