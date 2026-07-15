---
layout: post
title: "反向传播怎么验算：手写梯度和 finite difference gradient check"
date: 2026-06-28 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 NumPy MLP 的四个参数点做数值梯度检查，确认反向传播公式实现正确。"
tags: [deep-learning, backpropagation, gradient-check, teaching]
---
{% raw %}
> 主题：深度学习/AI 工程 / backpropagation / gradient check
> 本文 lab 已验证：gradient max relative error=3.00e-12，小于测试阈值 1e-6。

反向传播的代码很容易写错，而且错误不一定立刻报异常。gradient check 用一个简单思想检查梯度：把某个参数稍微加减一点，观察 loss 变化，与手写反向传播给出的梯度比较。这个检查慢，但非常适合教学和小模型调试。

典型错误包括忘记 batch 平均、矩阵转置方向写反、漏掉正则化项，或把 `tanh` 导数写错。它们都可能产生 shape 正确的数组，因此需要独立数值方法验证。

## 学习目标

1. 理解梯度表示 loss 对参数的局部变化率。
2. 写出 MLP 反向传播的关键梯度。
3. 用 finite difference 检查若干参数点。
4. 把 gradient check 作为训练前质量门。

## 先修知识

需要知道导数表示函数变化趋势。对矩阵求导不熟也可以先看代码路径。

## 核心模型

![反向传播怎么验算：手写梯度和 finite difference gradient check](/assets/diagrams/ai-engineering-backprop-gradient-check.svg)

反向传播从 loss 对 logits 的梯度开始，沿着 W2、tanh、W1 反向传回。finite difference 用 `(loss(theta+eps)-loss(theta-eps))/(2eps)` 近似同一个梯度。

## 沿计算图逐层标 shape

设 batch 大小为 `n`、输入维度 2、隐层宽度 `h=24`、类别数 2：

```text
X       (n, 2)
Z1      (n, h) = X @ W1 + b1
H       (n, h) = tanh(Z1)
logits  (n, 2) = H @ W2 + b2
loss    scalar
```

反向传播从 `(n,2)` 的 `diff` 开始，最终必须得到与四组参数完全同 shape 的梯度。

## 可信资料的关键结论

- PyTorch autograd 自动构建计算图并计算梯度；本包手写梯度是为了理解 autograd 在做什么。
- Finite difference 是小规模梯度实现的经典自检方法。
- 通过 gradient check 只能说明被检查路径局部一致，还需要训练和评估验证整体行为。

## 逐步实现

MLP forward：

```python
hidden = np.tanh(x @ W1 + b1)
logits = hidden @ W2 + b2
```

反向传播的核心：

```python
diff = (probs - one_hot(y)) / len(y)
grad_w2 = hidden.T @ diff
grad_hidden = diff @ W2.T
grad_z1 = grad_hidden * (1 - hidden ** 2)
grad_w1 = x.T @ grad_z1
```

完整 shape 流为：

```text
diff         (n,2)
grad_W2      (h,2) = H.T @ diff
grad_b2      (2,)  = sum(diff, axis=0)
grad_hidden  (n,h) = diff @ W2.T
grad_Z1      (n,h) = grad_hidden * (1-H²)
grad_W1      (2,h) = X.T @ grad_Z1
grad_b1      (h,)  = sum(grad_Z1, axis=0)
```

若加入 L2 正则化，`grad_W1` 和 `grad_W2` 还要分别加上 `weight_decay × W`。数值梯度计算 loss 时也必须包含同一项，否则两种梯度比较的函数并不相同。

数值检查：

```python
numeric = (loss_plus - loss_minus) / (2 * eps)
rel_error = abs(numeric - analytic) / max(1.0, abs(numeric), abs(analytic))
```

lab 输出：

```text
gradient_max_relative_error=3.00e-12
```

本次使用 seed 21 构造 8 条样本和 hidden size 5 的小模型，抽查 `W1`、`b1`、`W2`、`b2` 各一个参数，基础 loss 为 `0.8396392`。阈值为 `1e-6`，最大相对误差比阈值小约六个数量级。

测试命令为：

```bash
python -m unittest scripts/test_train.py
```

预期结果：

```text
Ran 1 test
OK
```

这个测试还运行完整训练并检查 MLP 是否超过线性 baseline。gradient check 只覆盖四个局部参数点；要扩大可信度，可以随机抽查更多索引，但无需在每个训练 epoch 执行。

## 常见错误

1. **训练不收敛就先调学习率。** 梯度实现错时，调参只会掩盖问题。
2. **用太大的 eps。** 数值梯度会偏离局部线性近似。
3. **全量参数都做 gradient check。** 小模型抽样检查足够发现主要公式错误。
4. **把 gradient check 当训练时常规步骤。** 它适合开发和教学，不适合大模型每步运行。

## 练习或延伸

1. 故意把 `1 - hidden ** 2` 改错，观察 gradient check 失败。
2. 增加一个 `W1[1, 2]` 的检查点。
3. 把 relative error 阈值改成 `1e-8`，观察是否仍然通过。

## 参考资料

- NumPy 文档：[numpy.matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html)
- PyTorch 教程：[Automatic Differentiation with torch.autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- PyTorch 文档：[torch.autograd.gradcheck](https://docs.pytorch.org/docs/stable/generated/torch.autograd.gradcheck.gradcheck.html)
- PyTorch 文档：[Numerical accuracy](https://docs.pytorch.org/docs/stable/notes/numerical_accuracy.html)

{% endraw %}
