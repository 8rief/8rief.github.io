---
layout: post
title: "链式法则到反向传播：一层 tanh 网络怎么传回梯度"
date: 2026-02-17 09:00:00 +0800
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

反向传播容易因“单样本公式”和“批量矩阵代码”混写而出错。当前实验使用 3 条样本、2 个输入、2 个输出；下面让每个 forward 张量和 backward 梯度保持明确 shape。

## 为什么要引入链式法则

设批量输入经过线性层 `Z=XW+b`，再经过 `tanh` 得到 `H`，最后和目标 `Y` 比较得到 loss。我们想知道某个权重 `W[0,0]` 改一点，loss 会怎样变。直接对整张网络展开公式会很乱，反向传播把局部导数沿计算图反向相乘。

## 正式定义

链式法则说明：如果 `L` 依赖 `h`，`h` 依赖 `z`，`z` 依赖 `W`，则 `dL/dW = dL/dh * dh/dz * dz/dW`。对 `tanh`，导数是 `1 - tanh(z)^2`。矩阵形式的反向传播把多个参数的偏导合并成数组运算。

## 直观模型

![链式法则到反向传播：一层 tanh 网络怎么传回梯度](/assets/diagrams/math-ai-chain-rule-backprop.svg)

forward 阶段保存中间值，backward 阶段从 loss 的导数开始，沿着计算图反向传播。每条边只负责自己的局部导数，整体梯度由局部导数相乘得到。

## 怎么算

核心 forward：

```python
x = np.array([[0.4, -1.1], [1.0, 0.2], [-0.3, 0.8]])
w = np.array([[0.7, -0.2], [0.5, 0.3]])
b = np.array([0.1, -0.4])
y = np.array([[1., 0.], [0., 1.], [1., 0.]])

z = x @ w + b
h = np.tanh(z)
loss = 0.5 * np.mean((h - y) ** 2)
```

核心 backward：

```python
d_h = (h - y) / h.size
d_z = d_h * (1 - h ** 2)
grad_w = x.T @ d_z
grad_b = d_z.sum(axis=0)
```

lab 用有限差分检查 `W[0,0]`：

```text
loss=0.423402
grad_w00_analytic=0.0154821388
grad_w00_numeric=0.0154821388
chain_rule_abs_error=2.81e-11
```

解析梯度和数值梯度高度一致，说明当前 forward cache、`tanh` 导数、矩阵维度和 outer product 方向都对齐。

本文代码现与 lab 的 batch-first 实现一致；单样本 `outer product` 只是这个矩阵公式的特例。

## 把 shape 沿图写出来

```text
X        (3,2)
W        (2,2)
b        (2,)
Z,H,Y    (3,2)
loss     scalar
dH,dZ    (3,2)
grad_W   (2,2) = X.T @ dZ
grad_b   (2,)  = sum(dZ, axis=0)
```

`loss=0.5*mean(...)` 对 6 个输出元素求平均，因此 `d_h` 必须除以 `h.size=6`。若误用 `len(h)=3`，梯度会整体放大两倍，shape 仍然正确，只有数值检查能暴露。

## `tanh` 局部导数来自哪里

因为 `H=tanh(Z)`，逐元素导数为 `1-H²`。当 `|Z|` 很大时，`H` 接近 ±1，导数接近 0；这就是饱和区梯度变小的原因。反向状态变化为：

```text
loss 对 H 的敏感度
  × tanh 在 Z 处的局部斜率
  -> loss 对 Z 的敏感度
  × X 的对应输入
  -> loss 对 W 的敏感度
```

偏置在每条样本上被广播，所以 `grad_b` 要沿样本轴求和。

## 有限差分怎样独立检查

```python
eps = 1e-6
original = w[0, 0]
w[0, 0] = original + eps
loss_plus = 0.5 * np.mean((np.tanh(x @ w + b) - y) ** 2)
w[0, 0] = original - eps
loss_minus = 0.5 * np.mean((np.tanh(x @ w + b) - y) ** 2)
w[0, 0] = original
numeric = (loss_plus - loss_minus) / (2 * eps)
```

恢复原参数很重要，否则后续检查会在被篡改的模型上进行。本次解析值与数值值之差 `2.81e-11`，支持这一局部梯度实现；其余参数和完整训练仍需额外测试。

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

## 练习与检查点

把激活函数从 `tanh` 改成 sigmoid，写出 `dz` 的表达式，并用有限差分检查一个权重。

## 参考资料
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- PyTorch 教程：[Automatic Differentiation with torch.autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- PyTorch 教程：[A Gentle Introduction to torch.autograd](https://docs.pytorch.org/tutorials/beginner/blitz/autograd_tutorial.html)
- NumPy 文档：[numpy.tanh](https://numpy.org/doc/stable/reference/generated/numpy.tanh.html)

{% endraw %}
