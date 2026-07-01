---
layout: post
title: "梯度下降和学习率：为什么一步一步能靠近最优点"
date: 2026-07-01 20:47:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "在一维凸二次函数上观察学习率、梯度方向和损失下降之间的关系。"
tags: [math, optimization, gradient-descent, teaching]
---
{% raw %}
> 主题：数学基础 / 优化 / 梯度下降
> 本文 lab 已验证：从 `x=-4` 出发，用学习率 `0.2` 优化二次函数，最终 `x≈2.5`、loss≈`1.0`。

梯度告诉我们局部方向，优化算法决定每一步走多远。学习率看似只是一个超参数，实际控制训练是否稳定、是否收敛、收敛速度多快。用一维二次函数先看清这个机制，比直接调深度学习模型更可靠。

## 问题从哪里来

给定损失函数 `f(x)=(x-2.5)^2+1`，最优点显然在 `x=2.5`。但真实模型通常没有这样明显的答案。梯度下降的思路是：在当前位置计算梯度，然后沿负梯度方向更新参数。若函数足够平滑、学习率合适，损失会逐步下降。

## 正式定义

梯度下降更新式是 `x_{t+1}=x_t - eta * grad f(x_t)`，其中 `eta` 是学习率。对二次函数 `f(x)=(x-2.5)^2+1`，梯度是 `2(x-2.5)`。当 `eta` 过大时，更新可能越过最优点并振荡；当 `eta` 过小时，收敛会很慢。

## 直观模型

![梯度下降和学习率：为什么一步一步能靠近最优点](/assets/diagrams/math-ai-gradient-descent-learning-rate.svg)

把损失曲线想成一个碗。当前位置的斜率告诉你哪边更低，学习率决定一步迈多大。合适的步长会逐渐接近碗底。

## 怎么算

核心循环：

```python
x = -4.0
eta = 0.2
for step in range(31):
    loss = (x - 2.5) ** 2 + 1
    grad = 2 * (x - 2.5)
    x = x - eta * grad
```

lab 输出摘要：

```text
optimization_start_x=-4.000
optimization_learning_rate=0.200
optimization_final_x=2.499999
optimization_final_loss=1.000000
```

前几步变化很大，后面逐渐变小，因为越接近最优点，梯度绝对值越小。这个例子也展示了为什么训练曲线常常前期下降快、后期下降慢。

## 有什么用

1. 神经网络训练循环的核心就是参数、loss、梯度、学习率和更新。
2. 学习率过大可能导致 loss 爆炸或来回震荡。
3. 学习率过小会让训练看似稳定但进展很慢。
4. 优化曲线是判断实现和超参数的第一批证据。

## 常见误区

1. **把梯度下降当保证全局最优的工具。** 非凸函数可能有鞍点和局部极小。
2. **只调 epoch 数。** 学习率不合适时，增加训练轮数可能没有意义。
3. **不记录 loss history。** 没有曲线就难以判断训练过程是否正常。
4. **所有参数共用同一尺度。** 特征标准化会明显影响优化稳定性。

## 检查点

把学习率改成 `0.01`、`0.6`、`1.1`，比较前 10 步 loss。解释慢收敛、振荡和发散分别是什么样子。

## 参考资料
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- PyTorch 教程：[Automatic Differentiation with torch.autograd](https://pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- NumPy 文档：[numpy.exp](https://numpy.org/doc/stable/reference/generated/numpy.exp.html)

{% endraw %}
