---
layout: post
title: "Sprague-Grundy 定理：用 mex 和 xor 分析公平组合游戏"
date: 2026-06-25 15:47:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从取石子游戏出发，解释 SG 值、mex、多个子游戏的异或合并，并用朴素胜负 DP 对照验证。"
tags: [algorithm, game-theory, sprague-grundy, mex, cplusplus]
---
{% raw %}
> 主题：Sprague-Grundy / Impartial Game / mex / xor / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

公平组合游戏中，双方可选行动相同，没有隐藏信息，不能行动者失败。很多取石子、图上移动棋子问题都能建成有向无环状态图。Sprague-Grundy 定理把每个状态映射成一个非负整数 SG 值；多个独立子游戏组合时，把 SG 值异或即可判断胜负。

## 学习目标

1. 用后继状态的 SG 集合计算 mex。
2. 解释 SG 值为 0 和必败态的关系。
3. 理解多个独立子游戏为什么使用 xor 合并。
4. 用取石子游戏实现 SG 表。
5. 用朴素胜负 DP 验证单堆和双堆结果。

## 核心模型

![Sprague-Grundy 计算流程](/assets/diagrams/algorithm-sprague-grundy-games.svg)

`mex` 是最小未出现非负整数。当前状态的 SG 值等于所有可达后继 SG 值集合的 mex。组合游戏的 SG 值等于各子游戏 SG 值的异或。

## C++ 实现片段

```cpp
int mex(std::vector<int> values) {
    std::sort(values.begin(), values.end());
    int g = 0;
    for (int x : values) {
        if (x == g) ++g;
        else if (x > g) break;
    }
    return g;
}
```

取石子状态按石子数天然拓扑有序，可以直接从小到大动态规划。一般 DAG 游戏也需要按后继已知的顺序计算。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
moves: 1 3 4
sg[0..10]: 0 1 0 1 2 3 2 0 1 0 1
heaps 7 10 12 xor=2 -> winning
```

测试检查 `{1}` 取法下 `sg[n]=n mod 2`，`{1,2,3}` 取法下 `sg[n]=n mod 4`。对 `{1,3,4}`，单堆结果与朴素必胜/必败 DP 对照，双堆组合结果与二维朴素 DP 对照。

## 正确性思路

若一个状态 SG 为 0，它的所有后继 SG 都非 0，当前玩家无法移动到必败态。若 SG 为 `g>0`，根据 mex 定义，后继集合包含 0，当前玩家可以移动到必败态。多个子游戏中，一步只改变一个分量；Nim 的异或不变量给出组合胜负判断。

## 常见错误

- 把 SG 值当作最少步数；SG 表示等价 Nim 堆大小。
- 在有环游戏上直接套 DAG 递推。
- 多个子游戏用普通加法合并；正确操作是异或。

## 练习

1. 为任意 DAG 游戏实现 SG 计算。
2. 寻找 `{1,3,4}` 取石子 SG 序列的周期。
3. 输出一个必胜局面的具体制胜移动。
4. 分析 Wythoff Game 与普通 SG DP 的规模差异。

## 参考资料

- [cp-algorithms: Sprague-Grundy theorem](https://cp-algorithms.com/game_theory/sprague-grundy-nim.html)
- [cppreference: std::sort](https://en.cppreference.com/w/cpp/algorithm/sort)
{% endraw %}
