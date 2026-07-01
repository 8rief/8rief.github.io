---
layout: post
title: "概率、期望和方差：把随机实验变成可比较数字"
date: 2026-07-01 20:43:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "从 Bernoulli 抛硬币实验出发，解释概率、期望、方差和模拟验证的关系。"
tags: [math, probability, statistics, teaching]
---
{% raw %}
> 主题：数学基础 / 概率 / 期望 / 方差
> 本文 lab 已验证：Bernoulli 随机变量理论均值 `0.300`，10000 次模拟均值约 `0.298`。

算法和系统里有大量随机现象：哈希冲突、抽样误差、A/B 测试波动、模型初始化、数据增强、网络延迟。概率把偶然现象转换成可以计算、比较和验证的对象。

## 问题从哪里来

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

rng = np.random.default_rng(7)
p = 0.3
samples = rng.binomial(1, p, size=10_000)
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

## 检查点

把 `size` 从 10000 改成 20，重复运行多次。观察样本均值为什么会比大样本更不稳定。

## 参考资料
- MIT OpenCourseWare：[6.041SC Probabilistic Systems Analysis and Applied Probability](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/)
- Penn State STAT 414：[Introduction to Probability Theory](https://online.stat.psu.edu/stat414/)
- NumPy 文档：[Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)

{% endraw %}
