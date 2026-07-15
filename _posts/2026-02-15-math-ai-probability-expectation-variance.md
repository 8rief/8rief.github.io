---
layout: post
title: "概率、期望和方差：把随机实验变成可比较数字"
date: 2026-02-15 18:00:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "从 Bernoulli 抛硬币实验出发，解释概率、期望、方差和模拟验证的关系。"
tags: [math, probability, statistics, teaching]
---
{% raw %}
> 主题：数学基础 / 概率 / 期望 / 方差
> 本文 lab 已验证：Bernoulli 随机变量理论均值 `0.300`，20000 次模拟均值约 `0.298`。

算法和系统里有大量随机现象：哈希冲突、抽样误差、A/B 测试波动、模型初始化、数据增强、网络延迟。概率把偶然现象转换成可以计算、比较和验证的对象。

一次模拟结果接近理论值，并不能证明实现必然正确；偏差究竟大不大，还要结合样本量计算样本均值的典型波动。本文把理论矩、模拟估计和标准误放到同一个例子里。

## 为什么要引入期望和方差

如果一个事件发生概率是 0.3，单次实验只能得到 0 或 1。一次结果无法说明长期水平。我们需要一个数字描述长期平均结果，也需要另一个数字描述波动大小。期望和方差正是这两个问题的答案。

## 正式定义

对离散随机变量 `X`，期望是 `E[X] = sum_x x P(X=x)`。方差是 `Var(X)=E[(X-E[X])^2]`。Bernoulli 随机变量只取 0 和 1，若 `P(X=1)=p`，则 `E[X]=p`，`Var(X)=p(1-p)`。

## 直观模型

![概率、期望和方差：把随机实验变成可比较数字](/assets/diagrams/math-ai-probability-expectation-variance.svg)

单次随机结果像一个跳动的点，期望是长期平均位置，方差是围绕平均位置的波动规模。样本量增加时，样本均值通常会靠近期望，但它不会每次都精确等于期望。

## 怎么算

NumPy 模拟：

```python
import numpy as np

rng = np.random.default_rng(9)
p = 0.3
samples = rng.binomial(1, p, size=20_000)
sample_mean = samples.mean()
sample_variance = samples.var()
```

lab 输出：

```text
bernoulli_sample_mean=0.298
theory_mean=0.300
sample_variance=0.2092
theory_variance=0.2100
```

模拟结果接近理论值，说明程序和公式在这个简单案例上互相支持。它也提醒我们：随机实验报告应固定 seed、说明样本量，并区分理论值和样本估计值。

这里的代码、seed 和样本量与当前 lab 一致。样本均值的理论标准误为：

```text
SE(mean) = sqrt(p(1-p)/n)
         = sqrt(0.3×0.7/20000)
         ≈ 0.00324
```

观察均值 `0.2979` 比理论均值低 `0.0021`，约为 `0.65` 个标准误，属于常见抽样波动。可以用代码计算：

```python
standard_error = np.sqrt(p * (1-p) / len(samples))
z = (sample_mean - p) / standard_error
print(f"se={standard_error:.5f}, z={z:.2f}")
```

预期约为 `se=0.00324, z=-0.65`。这比单纯说“0.298 很接近 0.300”提供了可比较尺度。

## 方差、样本方差和均值方差

三个量容易混淆：

- Bernoulli 单次结果的理论方差是 `p(1-p)=0.21`；
- 当前 20000 个 0/1 观测的总体式方差 `samples.var(ddof=0)` 约为 `0.20916`；
- 样本均值的方差是 `p(1-p)/n`，会随样本量增大而缩小。

`ddof=1` 常用于从样本估计未知总体方差；当前 lab 用 `ddof=0` 与已知 Bernoulli 理论方差直接对照。二者在 20000 个样本时差很小，但语义应写清楚。

缩小样本量能直接看到波动：

```python
for n in (20, 200, 20_000):
    means = [rng.binomial(1, p, size=n).mean() for _ in range(500)]
    print(n, np.std(means))
```

标准差应大致按 `1/sqrt(n)` 缩小。固定 seed 便于回归；严肃实验还应报告多个独立 seed 的分布。

## 有什么用

1. 训练集抽样、mini-batch 梯度和 dropout 都依赖随机变量。
2. 性能评估需要均值和波动，不能只给一次运行结果。
3. A/B 测试和实验对比需要知道差异是否超过随机波动。
4. 随机 baseline 能帮助判断复杂模型是否真的学到了结构。

## 常见误区

1. **把概率当单次保证。** 概率 0.3 不代表每 10 次必有 3 次发生。
2. **只报告均值。** 两个方法均值相近时，方差可能决定结论是否可靠。
3. **样本方差和理论方差混用。** 估计值来自样本，理论值来自分布假设。
4. **不固定随机种子。** 教学和回归测试中应固定 seed，真实实验可报告多个 seed。

## 练习与检查点

把 `size` 从 10000 改成 20，重复运行多次。观察样本均值为什么会比大样本更不稳定。

同时记录 500 次重复实验的样本均值标准差，并与 `sqrt(p(1-p)/20)` 比较；两者应处于相近量级。

## 参考资料
- MIT OpenCourseWare：[6.041SC Probabilistic Systems Analysis and Applied Probability](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/)
- Penn State STAT 414：[Introduction to Probability Theory](https://online.stat.psu.edu/stat414/)
- NumPy 文档：[Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)

{% endraw %}
