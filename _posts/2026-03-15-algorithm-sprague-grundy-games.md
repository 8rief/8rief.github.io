---
layout: post
title: "Sprague-Grundy 定理：用 mex 和 xor 分析公平组合游戏"
date: 2026-03-15 09:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从取石子游戏出发，解释 SG 值、mex、多个子游戏的异或合并，并用朴素胜负 DP 对照验证。"
tags: [algorithm, game-theory, sprague-grundy, mex, cplusplus]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithms-sprague-grundy-games/README.md`](/assets/labs/algorithms-sprague-grundy-games/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：Sprague-Grundy / Impartial Game / mex / xor / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

公平组合游戏中，双方可选行动相同，没有隐藏信息，不能行动者失败。很多取石子、图上移动棋子问题都能建成有向无环状态图。Sprague-Grundy 定理把每个状态映射成一个非负整数 SG 值；多个独立子游戏组合时，把 SG 值异或即可判断胜负。

直接为多个石子堆建立笛卡尔积状态会迅速膨胀：每堆有 n 个状态，三堆就可能有 `O(n³)` 个组合。SG 值先把每个独立子游戏压缩成一个 Nim 堆大小，再用 xor 合并。

## 学习目标

1. 用后继状态的 SG 集合计算 mex。
2. 解释 SG 值为 0 和必败态的关系。
3. 理解多个独立子游戏为什么使用 xor 合并。
4. 用取石子游戏实现 SG 表。
5. 用朴素胜负 DP 验证单堆和双堆结果。

## 核心模型

![Sprague-Grundy 计算流程](/assets/diagrams/algorithm-sprague-grundy-games.svg)

`mex` 是最小未出现非负整数。当前状态的 SG 值等于所有可达后继 SG 值集合的 mex。组合游戏的 SG 值等于各子游戏 SG 值的异或。

## 为什么要引入 mex 和 SG 值

只记录 win/lose 足以判断单个状态，却很难组合两个独立游戏。SG 值保留更丰富的“可达等价类”：

```text
SG(s) = mex({ SG(t) | s 可以一步到达 t })
```

`mex({0,1,3})=2`，重复值不影响集合。每个有限、无环、正常玩法的公平游戏状态都等价于一个大小为 `SG(s)` 的 Nim 堆。

适用条件必须同时满足：

1. 双方在同一状态拥有相同行动；
2. 游戏确定、完全信息；
3. 状态最终会终止，或至少递推图可按无环方式求值；
4. 采用 normal play，即无法行动者失败；
5. 组合游戏的一步只改变一个独立分量。

偏置游戏、misère 玩法或分量之间相互影响时，不能直接套用本文 xor 结论。

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

## 手算 `{1,3,4}` 的前几项

`sg[0]=0`，因为空堆没有后继。之后逐项计算：

| heap | 可达 SG 集合 | mex | sg |
| ---: | --- | ---: | ---: |
| 1 | `{sg[0]}={0}` | 1 | 1 |
| 2 | `{sg[1]}={1}` | 0 | 0 |
| 3 | `{sg[2],sg[0]}={0}` | 1 | 1 |
| 4 | `{sg[3],sg[1],sg[0]}={1,0}` | 2 | 2 |
| 5 | `{sg[4],sg[2],sg[1]}={2,0,1}` | 3 | 3 |
| 6 | `{sg[5],sg[3],sg[2]}={3,1,0}` | 2 | 2 |
| 7 | `{sg[6],sg[4],sg[3]}={2,1}` | 0 | 0 |

这与实验序列 `0 1 0 1 2 3 2 0 ...` 对齐。

## 实验输出怎样解释

```text
100% tests passed, 0 tests failed out of 1
moves: 1 3 4
sg[0..10]: 0 1 0 1 2 3 2 0 1 0 1
heaps 7 10 12 xor=2 -> winning
```

测试检查 `{1}` 取法下 `sg[n]=n mod 2`，`{1,2,3}` 取法下 `sg[n]=n mod 4`。对 `{1,3,4}`，单堆结果与朴素必胜/必败 DP 对照，双堆组合结果与二维朴素 DP 对照。

三堆 `7,10,12` 的 SG 值分别为 `0,1,3`，所以：

```text
0 xor 1 xor 3 = 2
```

xor 非零表示当前玩家存在一步把总 xor 变为 0，局面为 winning。demo 只判断胜负，没有输出具体制胜移动。

复跑：

```bash
./run_lab.sh
```

CTest 对单堆 0 到 50 与朴素 DP 对照，并穷举两堆大小 `0..12` 的 169 个组合，比较 xor 判定和二维状态 DP。

## 正确性思路

若一个状态 SG 为 0，它的所有后继 SG 都非 0，当前玩家无法移动到必败态。若 SG 为 `g>0`，根据 mex 定义，后继集合包含 0，当前玩家可以移动到必败态。多个子游戏中，一步只改变一个分量；Nim 的异或不变量给出组合胜负判断。

对组合局面，xor 为 0 时，任意一步只改变一个分量，其 SG 从 x 变到 y，新的 xor 为 `0 xor x xor y=x xor y`。合法一步不会保持同一 SG，因此结果非零。xor 非零时，取最高位为 1 的分量，总能把该分量移动到使总 xor 为 0 的更小 SG 值；SG 的 mex 定义保证对应后继存在。

## 复杂度

减法游戏计算到 n，每个状态枚举 M 个允许动作，再对至多 M 个值求 mex。当前排序版 mex 为 `O(M log M)`，总时间 `O(n M log M)`、空间 `O(n+M)`；用布尔标记可把单次 mex 降到 `O(M)`。

## 常见错误

- 把 SG 值当作最少步数；SG 表示等价 Nim 堆大小。
- 在有环游戏上直接套 DAG 递推。
- 多个子游戏用普通加法合并；正确操作是异或。
- 忘记 normal-play 边界，把“最后行动者失败”的 misère 游戏直接当普通 SG。
- 递归 DAG 时没有记忆化，重复计算同一状态。

## 练习

1. 为任意 DAG 游戏实现 SG 计算。
2. 寻找 `{1,3,4}` 取石子 SG 序列的周期。
3. 输出一个必胜局面的具体制胜移动。
4. 分析 Wythoff Game 与普通 SG DP 的规模差异。
5. 对局面 `7,10,12` 枚举所有合法一步，找出至少一个使 xor 变为 0 的动作。

## 参考资料

- [cp-algorithms: Sprague-Grundy theorem](https://cp-algorithms.com/game_theory/sprague-grundy-nim.html)
- [cppreference: std::sort](https://en.cppreference.com/w/cpp/algorithm/sort)
{% endraw %}
