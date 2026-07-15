---
layout: post
title: "随机化 Quickselect：只找第 k 小，不排序整组"
date: 2026-03-14 18:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从选择问题出发，解释随机 pivot、三路划分、只递归答案所在一侧和期望线性复杂度。"
tags: [algorithm, quickselect, randomized-algorithm, order-statistic, cplusplus]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithms-randomized-quickselect/README.md`](/assets/labs/algorithms-randomized-quickselect/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：Quickselect / Order Statistic / Randomized Algorithm / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

如果只需要第 `k` 小元素，完整排序会产生多余顺序信息。Quickselect 使用快速排序的划分思想：随机选择 pivot，把数组划成小于、等于、大于三段，然后只保留包含第 `k` 小的那一段继续处理。

例如只想找一百万个数的中位数，排序会建立全部排名；选择算法只维护“答案位于哪一侧”这一条信息。省去另一侧递归后，期望工作量从排序的 `O(n log n)` 降为 `O(n)`。

## 学习目标

1. 把选择问题和排序问题分开建模。
2. 实现三路划分，处理大量重复元素。
3. 说明随机化如何降低固定坏例风险。
4. 用排序结果作为 oracle 验证第 `k` 小。
5. 区分期望复杂度和最坏复杂度。

## 核心模型

![随机化 Quickselect 流程](/assets/diagrams/algorithm-randomized-quickselect.svg)

三路划分后，如果 `k` 落在等于 pivot 的区间内，pivot 就是答案；如果落在左段或右段，另一侧的所有元素都可以丢弃。

## 为什么要引入三路随机划分

两路划分在大量重复值下可能反复处理与 pivot 相等的元素。三路划分维护：

```text
[lo, lt)  < pivot
[lt, i)   = pivot
[i, gt)   尚未分类
[gt, hi)  > pivot
```

循环每步缩小未分类区间 `[i,gt)`；结束后等值段 `[lt,gt)` 可以整体判定。随机 pivot 则避免输入顺序固定地制造连续极端划分。

## C++ 实现片段

```cpp
int quickselect(std::vector<int> a, int k, std::mt19937& rng) {
    if (k < 0 || k >= static_cast<int>(a.size())) {
        throw std::out_of_range("k");
    }
    int lo = 0, hi = static_cast<int>(a.size());
    while (true) {
        int pivot = a[std::uniform_int_distribution<int>(lo, hi - 1)(rng)];
        int lt = lo, i = lo, gt = hi;
        while (i < gt) {
            if (a[i] < pivot) std::swap(a[lt++], a[i++]);
            else if (a[i] > pivot) std::swap(a[i], a[--gt]);
            else ++i;
        }
        if (k < lt) hi = lt;
        else if (k >= gt) lo = gt;
        else return pivot;
    }
}
```

参数 `a` 按值传入，所以函数会重排副本，调用方原数组保持不变。副本本身需要 `O(n)` 时间和空间；若改成引用，可省去复制，但接口必须明确会改变元素顺序。

## 手算一次划分

对数组 `9,1,5,7,3,3,8`，假设本轮 pivot 为 5，三路划分后的集合关系为：

```text
<5 : 1,3,3      对应排名 [0,3)
=5 : 5          对应排名 [3,4)
>5 : 9,7,8      对应排名 [4,7)
```

目标 `k=3` 使用 0-based 排名，落在等值段，因此立即返回 5。实际数组内部顺序可能因 swap 不同，但三个区间的关系必须成立。

## 实验输出怎样解释

```text
100% tests passed, 0 tests failed out of 1
array: 9 1 5 7 3 3 8
k=3 zero-based -> kth value=5
sorted check: 1 3 3 5 7 8 9
```

随机测试生成 500 个数组，选择随机 `k`，把 Quickselect 结果和排序后的第 `k` 个元素比较。重复元素样例检查等值段能否一次处理完。

固定样例同时检查 `k=0`、`k=3`、`k=6`，分别得到 1、5、9；50 个值都为 42 的数组检查等值段。随机数组长度为 1 到 120，元素范围为 -50 到 50，因此会自然产生负数和重复值。

复跑：

```bash
./run_lab.sh
```

demo 使用 seed 20260625，测试使用 seed 12345。固定 seed 让回归失败可重现，不改变随机 pivot 的期望复杂度分析。

## 正确性思路

划分后，左段元素都小于 pivot，中段都等于 pivot，右段都大于 pivot。第 `k` 小元素只可能落在一个区域内。算法每轮根据 `k` 与三段边界缩小候选区间，并保留答案所在区域。

随机 pivot 的期望分析来自规模缩减：pivot 进入中间排名区间时，下一轮规模会显著下降；坏 pivot 可能出现，但长期期望总处理量为线性。

每轮划分当前 m 个候选需要 `Θ(m)`。若 pivot 总能极端地选到最小或最大值，总工作量是 `n+(n-1)+...+1=Θ(n²)`。均匀随机 pivot 使各排名等概率，期望递推的解为 `O(n)`。

这里的期望针对算法内部随机性；最坏界仍是 `O(n²)`。需要确定性最坏线性时，可使用 median-of-medians，但常数和实现复杂度更高。

## 候选区间不变量

每轮开始时，原问题的第 k 小元素一定落在 `[lo,hi)`。划分后：

- `k<lt`：答案只可能在小于 pivot 段，令 `hi=lt`；
- `k>=gt`：答案只可能在大于 pivot 段，令 `lo=gt`；
- `lt<=k<gt`：第 k 小等于 pivot。

候选区间严格缩小，所以合法 k 下一定终止。

## 常见错误

- 两路划分在重复元素很多时退化明显。
- 混淆 0-based 与 1-based 的 `k`。
- 把随机化期望界当成确定性最坏界。
- 忽略非法 k；当前实现对负数、空数组或 `k>=n` 抛出 `out_of_range`。
- 以为返回后输入已经部分排序；当前按值接口只修改副本，且只保证第 k 个值，不保证其他位置顺序。

## 练习

1. 改成原地版本，并说明函数会重排输入。
2. 实现 median-of-medians，获得确定性最坏线性。
3. 用 Quickselect 找中位数并计算绝对偏差和。
4. 统计不同随机种子下的划分轮数。
5. 给随机测试增加空数组和越界 k 的异常断言。

## 参考资料

- [cp-algorithms: K-th order statistic in O(N)](https://cp-algorithms.com/sequences/k-th.html)
- [Princeton Algorithms: Quicksort](https://algs4.cs.princeton.edu/23quicksort/)
- [cppreference: std::mt19937](https://en.cppreference.com/w/cpp/numeric/random/mersenne_twister_engine)
{% endraw %}
