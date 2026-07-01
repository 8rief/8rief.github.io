---
layout: post
title: "链式法则到反向传播：一层 tanh 网络怎么传回梯度"
date: 2026-07-01 20:46:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "用一个小网络把链式法则展开成 forward cache 和 backward gradient 的工程结构。"
tags: [math, chain-rule, backpropagation, teaching]
---
{% raw %}
> 主题：数学基础 / 链式法则 / 反向传播
> 本文 lab 已验证：一层 `tanh` 网络中 `W[0,0]` 的解析梯度和数值梯度绝对误差约 `2.81e-11`。

神经网络由很多简单函数复合而成。单独看每个函数都不复杂，难点在于损失如何沿着这些函数一层层传回参数。链式法则把这个过程写成数学规则，反向传播把规则组织成可复用的计算流程。

## 问题从哪里来

设输入经过线性层 `z=Wx+b`，再经过 `tanh` 得到隐藏向量 `h`，最后和目标比较得到 loss。我们想知道某个权重 `W[0,0]` 改一点，loss 会怎样变。直接对整张网络展开公式会很乱，反向传播把局部导数沿计算图反向相乘。

## 正式定义

链式法则说明：如果 `L` 依赖 `h`，`h` 依赖 `z`，`z` 依赖 `W`，则 `dL/dW = dL/dh * dh/dz * dz/dW`。对 `tanh`，导数是 `1 - tanh(z)^2`。矩阵形式的反向传播把多个参数的偏导合并成数组运算。

## 直观模型

![链式法则到反向传播：一层 tanh 网络怎么传回梯度](/assets/diagrams/math-ai-chain-rule-backprop.svg)

forward 阶段保存中间值，backward 阶段从 loss 的导数开始，沿着计算图反向传播。每条边只负责自己的局部导数，整体梯度由局部导数相乘得到。

## 怎么算

核心 forward：

```python
z = W @ x + b
h = np.tanh(z)
loss = 0.5 * np.sum((h - target) ** 2)
```

核心 backward：

```python
dh = h - target
dz = dh * (1 - h ** 2)
dW = np.outer(dz, x)
db = dz
```

lab 用有限差分检查 `W[0,0]`：

```text
loss=0.423402
grad_w00_analytic=0.0154821388
grad_w00_numeric=0.0154821388
chain_rule_abs_error=2.81e-11
```

解析梯度和数值梯度高度一致，说明当前 forward cache、`tanh` 导数、矩阵维度和 outer product 方向都对齐。

## 有什么用

1. PyTorch autograd 的基本思想就是记录计算图并自动应用链式法则。
2. 手写小网络能帮助理解为什么 forward 中间值要保存。
3. 维度检查是反向传播 debug 的核心方法。
4. 梯度检查能给复杂模型的局部实现提供可信证据。

## 常见误区

1. **只背公式不看计算图。** 反向传播的清晰度来自节点、边和局部导数。
2. **忘记保存 forward 中间值。** `tanh` 的导数需要当前输出或输入。
3. **矩阵转置方向写错。** `np.outer(dz, x)` 和 `np.outer(x, dz)` 形状不同。
4. **把 autograd 当黑箱。** 自动微分减少手写梯度，但不消除对链式法则的理解需求。

## 检查点

把激活函数从 `tanh` 改成 sigmoid，写出 `dz` 的表达式，并用有限差分检查一个权重。

## 参考资料
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- PyTorch 教程：[Automatic Differentiation with torch.autograd](https://pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- NumPy 文档：[numpy.exp](https://numpy.org/doc/stable/reference/generated/numpy.exp.html)

{% endraw %}
