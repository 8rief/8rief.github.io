---
layout: post
title: "基础 DP 题型：先写状态，再检查转移顺序"
date: 2026-03-08 09:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用零钱、0/1 背包和网格路径讲清一维 DP、二维 DP 与空间压缩的基本边界。"
tags: [algorithm, dynamic-programming, knapsack, cpp, testing]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithm-practical-foundations/README.md`](/assets/labs/algorithm-practical-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：算法实用基础 / dynamic programming / state transition  
> 本文 lab 已验证：`min_coins({1,3,4}, 6)=2`，容量 5 的 0/1 背包最优值为 9。

动态规划最容易学成“看到数组就填表”。更可靠的做法是先写清楚状态表示什么，再写从哪些旧状态转移，最后决定遍历顺序。本文只补基础题型：一维最短代价、0/1 背包、网格路径计数。

DP 数组的下标、初始化和遍历顺序共同定义算法。只抄转移式而不写状态语义，往往会把 0/1 选择写成可重复选择，或让不可达状态参与计算。

## 问题模型

DP 适合有重复子问题和最优子结构的问题。零钱问题问凑出金额 x 的最少硬币数；0/1 背包问容量 c 下的最大价值；网格路径问到达每个格子的路径数。它们都能把大问题拆成更小状态。

## 为什么需要先定义状态

一条可检查的 DP 设计应依次回答：

```text
dp 下标表示什么？
dp 值表示什么？
初始状态是什么？
当前状态依赖哪些旧状态？
按什么顺序保证旧状态已经正确？
最终答案位于哪里？
```

状态定义变化，转移方向也会变化；遍历顺序属于正确性条件，不只是代码优化。

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

## 三个固定例子怎样填表

零钱 `{1,3,4}`、amount=6：

```text
x:      0 1 2 3 4 5 6
dp[x]:  0 1 2 1 1 2 2
```

`dp[6]=2` 来自 `dp[3]+1`，对应 3+3。不可达值使用 `INF`；源码取 `max_int/4`，避免执行 `INF+1` 时接近溢出。

0/1 背包物品 `(weight,value)=(2,4),(3,5),(4,6)`、容量 5，最优选择前两件，价值 9。容量倒序使当前物品只读取本轮更新前的较小容量：

```text
for cap = capacity down to weight
```

若改为正序，重量 2 的同一件物品会先更新 `dp[2]`，随后又被用于更新 `dp[4]`，语义变成完全背包。

3×3 网格中心为障碍：

```text
...
.#.
...
```

只能沿上边+右边或左边+下边绕行，共 2 条路径。

## 测试输出怎样解释

lab 输出：

```text
dp_min_coins_6=2 knapsack_capacity_5=9
```

测试覆盖了不可达金额、背包容量边界、障碍网格路径数。DP 的常见错误来自初始化、遍历方向和不可达状态。把小规模输入用暴力枚举对照，是定位 DP 错误的有效方法。

复跑：

```bash
./run_lab.sh
```

本文相关四项断言为：零钱结果 2、不可达金额返回 -1、背包结果 9、障碍网格路径数 2。

## 输入边界

当前教学函数假设 amount/capacity 非负、硬币和重量为正、weights 与 values 等长、网格非空且矩形。公共库接口应在入口验证这些条件；否则负 amount 会转换成异常大的 vector 大小，空网格会触发越界。

## 常见错误

1. `dp[0]` 未初始化为问题的单位状态。
2. 不可达状态仍参与 `+1` 或加价值，产生伪答案或溢出。
3. 0/1 背包容量正序，意外重复使用同一物品。
4. 障碍格没有清零，旧路径数穿过障碍传播。
5. 只检查最终答案，不用小表观察每个状态。

## 练习

1. 把零钱问题改成统计方案数，并说明遍历顺序变化。
2. 写二维 0/1 背包，再和一维压缩结果对照。
3. 给网格路径增加只能向右或向下走的路径恢复。
4. 为三种 DP 各写一个小规模暴力 oracle，做随机对照。

## 参考资料

- CP-Algorithms：[Introduction to Dynamic Programming](https://cp-algorithms.com/dynamic_programming/intro-to-dp.html)
- MIT 6.006：[Dynamic Programming I](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-19-dynamic-programming-i-fibonacci-shortest-paths/)
- cppreference：[std::numeric_limits](https://en.cppreference.com/w/cpp/types/numeric_limits)

{% endraw %}
